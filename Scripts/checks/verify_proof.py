#!/usr/bin/env python3
"""Coast proof-file verifier — the deterministic CI gate (D23, D30 net 1).

Implements coast-ledger-and-proof-spec.md §8: pure functions of the PR head
tree, the PR base tree, the branch name, and the git commit graph. No
network, no ledger access, no model calls. Ships in the scaffolded repo under
the GOVERNING class (agents cannot touch it — D12).

Usage: verify_proof.py <base_sha> <head_sha> <branch_name>
Run from the repository root of a full-history checkout at <head_sha>.

Checks (numbering per the spec):
  Both PRs:  1 existence+schema, 2 identity binding, 3 completeness,
             4 chain integrity, 8 predecessor superset.
  PR #2:     5 sensitive-diff => approval present, 6 work-items vs approved
             items, 7 approve-before-build ordering, 9 amendment closure.

Exit 0 = all pass. Any failure prints a machine-readable line
FAIL {check} {subject}: {reason} and exits 1.

Canonical JSON form (spec §6.0) is exactly:
    json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
"""

import hashlib
import json
import re
import subprocess
import sys
import unicodedata

PLAN_SCHEMA_VERSION = 1
PROOF_SCHEMA_VERSION = 1
AMENDMENT_SCHEMA_VERSION = 1
TICKET_SCHEMA_VERSION = 1

# Coast-written path classes excluded from check 6 (F2 §3.2 PLANS/GENERATED).
COAST_WRITTEN_PREFIXES = ("plans/", "docs/diagrams/", "Modules/Data/Generated/")
COAST_WRITTEN_EXACT = ("Package.resolved",)

failures = []


def fail(check, subject, reason):
    failures.append({"check": check, "subject": subject, "reason": reason})
    print(f"FAIL {check} {subject}: {reason}")


def ok(check, detail=""):
    print(f"PASS {check}" + (f" ({detail})" if detail else ""))


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256hex(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def item_content_hash(item):
    return sha256hex(canonical({
        "kind": item["kind"], "target": item["target"], "description": item["description"],
    }))


def match_form(path):
    """Case- and NFC-normalization-insensitive comparison form (F2 §3.1)."""
    return unicodedata.normalize("NFC", path).lower()


def target_covers(target, path):
    """F3 §4.3: exact match, or a '/**' glob covering the path."""
    t, p = match_form(target), match_form(path)
    if t.endswith("/**"):
        prefix = t[:-2]  # keep the trailing "/"
        return p.startswith(prefix) or p == prefix[:-1]
    return t == p


def glob_matches(pattern, path):
    """Full glob for sensitivity bindings: ** crosses directories, * stays
    within a component. Mirrors Coast's Glob (CoastEnforcement)."""
    pat = match_form(pattern)
    out = "^"
    i = 0
    while i < len(pat):
        c = pat[i]
        if c == "*":
            if pat[i:i + 3] == "**/":
                out += "(?:.*/)?"
                i += 3
                continue
            if pat[i:i + 2] == "**" and i + 2 == len(pat) and i >= 1 and pat[i - 1] == "/":
                out = out[:-1] + "(?:/.*)?"
                i += 2
                continue
            if pat[i:i + 2] == "**":
                out += ".*"
                i += 2
                continue
            out += "[^/]*"
            i += 1
            continue
        out += re.escape(c) if c != "/" else "/"
        i += 1
    out += "$"
    return re.fullmatch(out, match_form(path)) is not None


def git(*args, check=True):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def git_show_bytes(sha, path):
    result = subprocess.run(["git", "show", f"{sha}:{path}"], capture_output=True)
    return result.stdout if result.returncode == 0 else None


def read_head_bytes(path):
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError:
        return None


def is_currently_approved(entry):
    verdicts = entry.get("verdicts", [])
    return bool(verdicts) and verdicts[-1].get("verdict") == "approved"


def has_security_approval(entry):
    return any(v.get("verdict") == "approved" and v.get("approver_role") == "security-approval"
               for v in entry.get("verdicts", []))


def main():
    if len(sys.argv) != 4:
        print("usage: verify_proof.py <base_sha> <head_sha> <branch_name>")
        return 2
    base_sha, head_sha, branch = sys.argv[1], sys.argv[2], sys.argv[3]

    if not branch.startswith("feature/"):
        fail("check2", branch, "branch name must be feature/<feature_id>")
        return finish()
    feature_id = branch[len("feature/"):]
    plan_path = f"plans/{feature_id}/plan.json"
    proof_path = f"plans/{feature_id}/proof.json"
    ticket_path = f"plans/{feature_id}/ticket.json"

    # ---- Check 1 — existence + schema + canonical form -------------------
    docs = {}
    for name, path, version_key, version in [
        ("plan", plan_path, "plan_schema_version", PLAN_SCHEMA_VERSION),
        ("proof", proof_path, "proof_schema_version", PROOF_SCHEMA_VERSION),
        ("ticket", ticket_path, "ticket_schema_version", TICKET_SCHEMA_VERSION),
    ]:
        raw = read_head_bytes(path)
        if raw is None:
            fail("check1", path, "missing at PR head")
            continue
        try:
            value = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as err:
            fail("check1", path, f"does not parse: {err}")
            continue
        if value.get(version_key) != version:
            fail("check1", path, f"{version_key} != {version}")
        if canonical(value) != raw:
            fail("check1", path, "not in canonical form (§6.0 byte-exact rule)")
        docs[name] = value
    if set(docs) != {"plan", "proof", "ticket"}:
        return finish()
    plan, proof, ticket = docs["plan"], docs["proof"], docs["ticket"]

    required_plan = ["feature_id", "plan_version", "ticket_ref", "base_commit",
                     "declared_scope", "db_change", "items", "acceptance_criteria"]
    for key in required_plan:
        if key not in plan:
            fail("check1", plan_path, f"missing required field {key}")
    for key in ["feature_id", "purpose", "plan_version", "plan_file_hash",
                "base_commit", "export_seq", "items"]:
        if key not in proof:
            fail("check1", proof_path, f"missing required field {key}")
    if failures:
        return finish()
    ok("check1")

    purpose = proof["purpose"]

    # ---- Check 2 — identity binding --------------------------------------
    plan_bytes = read_head_bytes(plan_path)
    if proof["feature_id"] != plan["feature_id"] or plan["feature_id"] != feature_id:
        fail("check2", "feature_id", f"proof/plan/branch disagree: {proof['feature_id']}/{plan['feature_id']}/{feature_id}")
    if proof["plan_version"] != plan["plan_version"]:
        fail("check2", "plan_version", "proof and plan disagree")
    if proof["plan_file_hash"] != sha256hex(plan_bytes):
        fail("check2", "plan_file_hash", "does not match the plan file bytes at PR head")
    if proof["base_commit"] != plan["base_commit"]:
        fail("check2", "base_commit", "proof and plan disagree")
    if ticket.get("feature_id") != plan["feature_id"] or ticket.get("ticket_ref") != plan["ticket_ref"]:
        fail("check2", ticket_path, "ticket feature_id/ticket_ref do not match the plan")

    plan_items = {item["item_id"]: item for item in plan["items"]}
    for item in plan["items"]:
        if item.get("content_hash") != item_content_hash(item):
            fail("check2", item["item_id"], "plan item content_hash does not recompute")

    for entry in proof["items"]:
        recomputed = item_content_hash(entry)
        if entry.get("content_hash") != recomputed:
            fail("check2", entry["item_id"], "proof item content_hash does not recompute")
        if entry.get("origin") == "plan":
            plan_item = plan_items.get(entry["item_id"])
            if plan_item is None:
                fail("check2", entry["item_id"], "plan-origin proof item not present in plan file")
            else:
                for field in ["kind", "target", "description", "sensitive", "content_hash"]:
                    if entry.get(field) != plan_item.get(field):
                        fail("check2", entry["item_id"], f"field {field} differs between proof and plan")
        elif entry.get("origin") == "drift":
            amendment_path = entry.get("amendment_file")
            if not amendment_path:
                fail("check2", entry["item_id"], "drift item names no amendment_file")
                continue
            raw = read_head_bytes(amendment_path)
            if raw is None:
                fail("check2", amendment_path, "referenced amendment file missing at PR head")
                continue
            amendment = json.loads(raw.decode("utf-8"))
            if canonical(amendment) != raw:
                fail("check2", amendment_path, "amendment not in canonical form")
            if amendment.get("amendment_schema_version") != AMENDMENT_SCHEMA_VERSION:
                fail("check2", amendment_path, "bad amendment_schema_version")
            embedded = amendment.get("item", {})
            for field in ["item_id", "kind", "target", "description", "content_hash"]:
                if embedded.get(field) != entry.get(field):
                    fail("check2", amendment_path, f"embedded item field {field} differs from proof item")
    if not [f for f in failures if f["check"] == "check2"]:
        ok("check2")

    # ---- Check 3 — completeness (approve-before-work) ---------------------
    proof_by_id = {entry["item_id"]: entry for entry in proof["items"]}
    for item_id in plan_items:
        entry = proof_by_id.get(item_id)
        if entry is None:
            fail("check3", item_id, "plan item has no proof entry")
            continue
        if not is_currently_approved(entry):
            fail("check3", item_id, "not currently approved (last verdict must be approved)")
        last = entry["verdicts"][-1] if entry.get("verdicts") else {}
        if last.get("verdict") == "approved" and last.get("item_content_hash") not in (None, entry.get("content_hash")):
            fail("check3", item_id, "operative verdict binds a different item content hash")
    for entry in proof["items"]:
        if entry.get("origin") == "drift":
            if purpose == "plan-pr":
                fail("check3", entry["item_id"], "drift item present on plan PR (impossible before implementation)")
            elif not is_currently_approved(entry):
                fail("check3", entry["item_id"], "drift item not currently approved")
        if entry.get("sensitive") and not has_security_approval(entry):
            fail("check3", entry["item_id"], "sensitive item lacks an approved security-approval verdict")
    if not [f for f in failures if f["check"] == "check3"]:
        ok("check3")

    # ---- Check 4 — chain integrity ----------------------------------------
    seen_approval_ids = set()
    for entry in proof["items"] + proof.get("superseded_items", []):
        verdicts = entry.get("verdicts", [])
        expected_first = "drift" if entry.get("origin") == "drift" else "initial"
        prior_ids = set()
        prior_ts = ""
        for index, verdict in enumerate(verdicts):
            approval_id = verdict.get("approval_id")
            if approval_id in seen_approval_ids:
                fail("check4", entry["item_id"], f"approval_id {approval_id} not unique file-wide")
            seen_approval_ids.add(approval_id)
            timestamp = verdict.get("timestamp", "")
            if timestamp < prior_ts:
                fail("check4", entry["item_id"], "verdict timestamps decrease")
            prior_ts = timestamp
            if index == 0:
                if verdict.get("trigger") != expected_first:
                    fail("check4", entry["item_id"], f"first trigger must be {expected_first}, got {verdict.get('trigger')}")
            else:
                if verdict.get("trigger") not in ("rejection-revision", "staleness"):
                    fail("check4", entry["item_id"], f"later trigger invalid: {verdict.get('trigger')}")
                if verdict.get("supersedes") not in prior_ids:
                    fail("check4", entry["item_id"], "supersedes must name an earlier approval_id of the same item")
            if verdict.get("verdict") == "rejected" and index < len(verdicts) - 1:
                superseded_later = any(v.get("supersedes") == approval_id for v in verdicts[index + 1:])
                if not superseded_later:
                    fail("check4", entry["item_id"], "non-final rejected verdict never superseded")
            prior_ids.add(approval_id)
    if not [f for f in failures if f["check"] == "check4"]:
        ok("check4")

    # ---- Check 8 — predecessor superset (replay/rollback protection) ------
    old_raw = git_show_bytes(base_sha, proof_path)
    if old_raw is not None:
        old = json.loads(old_raw.decode("utf-8"))
        if old.get("feature_id") != proof["feature_id"]:
            fail("check8", proof_path, "feature_id changed against predecessor")
        if not (isinstance(proof.get("export_seq"), int) and proof["export_seq"] > old.get("export_seq", -1)):
            fail("check8", proof_path, "export_seq must strictly increase")
        new_verdicts = {}
        for entry in proof["items"] + proof.get("superseded_items", []):
            for verdict in entry.get("verdicts", []):
                new_verdicts[verdict.get("approval_id")] = canonical(verdict)
        for entry in old.get("items", []) + old.get("superseded_items", []):
            for verdict in entry.get("verdicts", []):
                aid = verdict.get("approval_id")
                if aid not in new_verdicts:
                    fail("check8", aid or "?", "verdict present in predecessor missing from new proof")
                elif new_verdicts[aid] != canonical(verdict):
                    fail("check8", aid, "verdict bytes altered against predecessor")
    if not [f for f in failures if f["check"] == "check8"]:
        ok("check8", "no predecessor" if old_raw is None else "superset holds")

    if purpose != "implementation-pr":
        return finish()

    # ---- PR #2 only -------------------------------------------------------
    diff = git("diff", "--name-status", f"{base_sha}..{head_sha}").strip()
    changed, deleted = [], []
    for line in diff.splitlines():
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R"):
            deleted.append(parts[1])
            changed.append(parts[2])
        elif status == "D":
            deleted.append(parts[1])
        else:
            changed.append(parts[-1])
    all_touched = changed + deleted

    def coast_written(path):
        return path.startswith(COAST_WRITTEN_PREFIXES) or path in COAST_WRITTEN_EXACT

    approved_entries = [e for e in proof["items"] if is_currently_approved(e)]
    approved_drift = [e for e in approved_entries if e.get("origin") == "drift"]
    approved_removals = [e for e in approved_entries if e.get("kind") == "removal"]

    # Check 5 — sensitive-diff ⇒ approval present. Globs load from the PR
    # BASE (a PR cannot relax the globs it is judged by — D54/D12).
    globs_raw = git_show_bytes(base_sha, ".coast/sensitivity-globs.json")
    sensitivity_globs = json.loads(globs_raw.decode("utf-8")) if globs_raw else []
    for path in all_touched:
        hits = [g for g in sensitivity_globs if glob_matches(g, path)]
        if not hits:
            continue
        covering = [e for e in approved_entries
                    if target_covers(e["target"], path) and e.get("sensitive") and has_security_approval(e)]
        if not covering:
            fail("check5", path, f"matches sensitivity glob {hits[0]} with no covering approved sensitive item")
    if not [f for f in failures if f["check"] == "check5"]:
        ok("check5")

    # Check 6 — work-items vs approved items (the D30 structural net).
    scope = plan.get("declared_scope", [])
    for path in all_touched:
        if coast_written(path):
            continue
        in_scope = any(target_covers(g, path) for g in scope)
        drift_covered = any(target_covers(e["target"], path) for e in approved_drift)
        if not in_scope and not drift_covered:
            fail("check6a", path, "outside declared_scope and not covered by an approved drift item")
    for path in deleted:
        if coast_written(path):
            continue
        if not any(match_form(e["target"]) == match_form(path) for e in approved_removals):
            fail("check6b", path, "deleted without an exactly-matching approved removal item")

    # Check 6c — new top-level non-private type declarations map to approved
    # module/type/ui-component items covering the declaring file.
    # M1 slot filler (D5): a deterministic scan of ADDED lines for column-0
    # type declarations. The v1 filler is the Swift symbol graph
    # (swift-symbolgraph-extract) and lands with M2's diagram tooling.
    decl_re = re.compile(
        r"^(?:@\w+(?:\([^)]*\))?\s+)*"
        r"(?!private\b)(?!fileprivate\b)(?:(?:public|internal|package|open)\s+)?"
        r"(?:final\s+)?(class|struct|enum|actor|protocol)\s+(\w+)")
    structural_kinds = ("module", "type", "ui-component")
    for path in changed:
        if coast_written(path) or not path.endswith(".swift"):
            continue
        # Test-target types are exempt: post-work unit tests are below plan
        # resolution by design (D24 — S11 adds tests the plan never itemizes),
        # and the v1 symbol-graph filler extracts app modules, not test
        # targets. SPM convention: test targets live under Tests/.
        if path.startswith("Tests/"):
            continue
        added = git("diff", f"{base_sha}..{head_sha}", "--unified=0", "--", path)
        for line in added.splitlines():
            if not line.startswith("+") or line.startswith("+++"):
                continue
            m = decl_re.match(line[1:])
            if not m:
                continue
            covered = any(e.get("kind") in structural_kinds and target_covers(e["target"], path)
                          for e in approved_entries)
            if not covered:
                fail("check6c", f"{path}#{m.group(2)}",
                     f"new top-level {m.group(1)} not covered by an approved module/type/ui-component item")
    if not [f for f in failures if f["check"].startswith("check6")]:
        ok("check6")

    # Check 7 — approve-before-build ordering (D68), first-parent order.
    fp_commits = git("rev-list", "--first-parent", "--reverse", f"{base_sha}..{head_sha}").split()
    order = {sha: index for index, sha in enumerate(fp_commits)}

    def first_parent_commits_touching(path):
        out = git("log", "--first-parent", "--format=%H", f"{base_sha}..{head_sha}", "--", path)
        return [sha for sha in out.split() if sha in order]

    for entry in approved_drift:
        amendment_path = entry.get("amendment_file")
        adds = git("log", "--first-parent", "--diff-filter=A", "--format=%H",
                   f"{base_sha}..{head_sha}", "--", amendment_path).split()
        if not adds:
            fail("check7", entry["item_id"], "amendment file was never added in this PR")
            continue
        amendment_index = order.get(adds[-1], 10 ** 9)
        for sha in first_parent_commits_touching(entry["target"]):
            if order[sha] < amendment_index:
                fail("check7", entry["item_id"],
                     f"commit {sha[:8]} touches the drift target before the amendment commit (built-then-approved)")
    if not [f for f in failures if f["check"] == "check7"]:
        ok("check7")

    # Check 10 — single-author rule (D94: a rogue commit by any identity
    # other than Coast's committer stands out and fails the gate).
    authors = set(git("log", "--format=%an <%ae>", f"{base_sha}..{head_sha}").strip().splitlines())
    if len(authors) > 1:
        fail("check10", "authors", f"PR contains commits from multiple authors: {sorted(authors)}")
    elif not [f for f in failures if f["check"] == "check10"]:
        ok("check10", f"single author: {next(iter(authors), '?')}")

    # Check 9 — amendment closure (no orphan amendments, no unamended drift).
    amendment_dir = f"plans/{feature_id}/amendments"
    listed = git("ls-tree", "-r", "--name-only", head_sha, "--", amendment_dir).split()
    drift_files = {e.get("amendment_file") for e in proof["items"] if e.get("origin") == "drift"}
    for path in listed:
        if path not in drift_files:
            fail("check9", path, "amendment file has no drift item in the proof")
    for path in drift_files:
        if path and path not in listed:
            fail("check9", path, "drift item's amendment file missing from the tree")
    if not [f for f in failures if f["check"] == "check9"]:
        ok("check9")

    return finish()


def finish():
    if failures:
        print(json.dumps({"result": "fail", "failures": failures}))
        return 1
    print(json.dumps({"result": "pass"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
