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
# docs/api/, docs/modules/, docs/features/index.md: the docs generator's
# output (deltas 31b) — mirrors PathClasses.v1iOSDefaults.generated.
COAST_WRITTEN_PREFIXES = ("plans/", "docs/diagrams/", "Modules/Data/Generated/",
                          "docs/api/", "docs/modules/")
COAST_WRITTEN_EXACT = ("Package.resolved", "docs/features/index.md")

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


_git_show_cache = {}


def git_show_bytes(sha, path):
    # Memoized: a Words batch puts N changes to ONE catalog in one ticket,
    # and dc4 reads each change's catalog from both trees — without the
    # cache that is 2N identical subprocess calls per merge gate.
    key = (sha, path)
    if key not in _git_show_cache:
        result = subprocess.run(["git", "show", f"{sha}:{path}"], capture_output=True)
        _git_show_cache[key] = result.stdout if result.returncode == 0 else None
    return _git_show_cache[key]


def read_head_bytes(path):
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError:
        return None


STRING_CATALOG_SUFFIXES = (".strings", ".xcstrings")

STRINGS_VALUE_RE = r'"({key})"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;'


def strings_unescape(value):
    """Mirror of Coast's DirectChangeApplier.unescaped (single pass)."""
    out, i = [], 0
    while i < len(value):
        ch = value[i]
        if ch == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            mapped = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt)
            if mapped is not None:
                out.append(mapped)
                i += 2
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def catalog_value(raw, path, key, locale, plural_variation=None):
    """The current text for `key` in a catalog blob, or (None, reason).
    `plural_variation` reads that CLDR category's value instead of the plain
    stringUnit (Words C1 plural changes); .strings files have no plurals."""
    if raw is None:
        return None, "file missing"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, "not UTF-8"
    if path.endswith(".xcstrings"):
        try:
            doc = json.loads(text)
        except ValueError:
            return None, "not valid JSON"
        loc = locale or doc.get("sourceLanguage")
        localization = (doc.get("strings", {}).get(key, {})
                        .get("localizations", {}).get(loc or "", {}))
        if plural_variation:
            unit = (localization.get("variations", {}).get("plural", {})
                    .get(plural_variation, {}).get("stringUnit", {}))
            value = unit.get("value")
            return ((value, None) if value is not None
                    else (None, f"key has no {loc} {plural_variation} plural variation"))
        unit = localization.get("stringUnit", {})
        value = unit.get("value")
        return (value, None) if value is not None else (None, f"key has no {loc} value")
    if plural_variation:
        return None, "plural forms don't live in .strings files"
    matches = re.findall(STRINGS_VALUE_RE.format(key=re.escape(key)), text)
    if len(matches) != 1:
        return None, f"key appears {len(matches)} times"
    return strings_unescape(matches[0][1]), None


def planless_common_checks(check, proof, proof_raw, proof_path, plan_path,
                           ticket_path, required_fields, no_plan_reason):
    """Shared check-1 body for every PLANLESS proof purpose (direct-change,
    bug-fix): canonical form, schema version, required fields, NO plan file,
    and the ticket file's own existence/schema/canonical checks. One copy —
    a schema bump or canonical-rule change lands on both paths at once.
    Returns the parsed ticket, or None when a hard failure stops the check.
    """
    if canonical(proof) != proof_raw:
        fail(check, proof_path, "not in canonical form (§6.0 byte-exact rule)")
    if proof.get("proof_schema_version") != PROOF_SCHEMA_VERSION:
        fail(check, proof_path, f"proof_schema_version != {PROOF_SCHEMA_VERSION}")
    for key in required_fields:
        if key not in proof:
            fail(check, proof_path, f"missing required field {key}")
    if read_head_bytes(plan_path) is not None:
        fail(check, plan_path, no_plan_reason)
    ticket_raw = read_head_bytes(ticket_path)
    if ticket_raw is None:
        fail(check, ticket_path, "missing at PR head")
        return None
    try:
        ticket = json.loads(ticket_raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as err:
        fail(check, ticket_path, f"does not parse: {err}")
        return None
    if ticket.get("ticket_schema_version") != TICKET_SCHEMA_VERSION:
        fail(check, ticket_path, f"ticket_schema_version != {TICKET_SCHEMA_VERSION}")
    if canonical(ticket) != ticket_raw:
        fail(check, ticket_path, "not in canonical form")
    return ticket


def planless_identity_check(check, proof, ticket, ticket_path, feature_id):
    """Shared check-2 body for planless proofs: proof/ticket/PR agree."""
    if proof["feature_id"] != feature_id or ticket.get("feature_id") != feature_id:
        fail(check, "feature_id", f"proof/ticket/PR disagree: {proof['feature_id']}/{ticket.get('feature_id')}/{feature_id}")
    if not ticket.get("ticket_ref"):
        fail(check, ticket_path, "ticket_ref missing")
    if not failures:
        ok(check)


def verify_direct_change(base_sha, head_sha, feature_id, proof, proof_raw,
                         proof_path, ticket_path, plan_path):
    """The planless direct-change PR (coast-ticket-types-spec.md §3, D116).
    The proof IS the ticketed edit; these checks make the trees agree with it:
      dc1 existence + schema (and NO plan file — a direct change has none)
      dc2 identity binding
      dc3 diff scope — only the declared catalogs (+ the proof/ticket) changed
      dc4 content match — base tree said the expected text, head says the new
    """
    # ---- dc1 — existence + schema + canonical form -----------------------
    ticket = planless_common_checks(
        "dc1", proof, proof_raw, proof_path, plan_path, ticket_path,
        ["feature_id", "purpose", "export_seq", "changes", "allowed_files"],
        "a direct-change PR must not carry a plan file")
    changes = proof.get("changes", [])
    if not isinstance(changes, list) or not changes:
        fail("dc1", proof_path, "changes must be a non-empty list")
        return
    plural_categories = {"zero", "one", "two", "few", "many", "other"}
    for change in changes:
        for key in ["catalog", "key", "expected_current", "new_value"]:
            if key not in change:
                fail("dc1", proof_path, f"a change is missing required field {key}")
        variation = change.get("plural_variation")
        if variation is not None and variation not in plural_categories:
            fail("dc1", proof_path, f"'{variation}' is not a plural category")
        if change.get("expected_current") is None and variation is None:
            fail("dc1", proof_path,
                 "expected_current is null on a plain change — only a plural variation being added may omit it")
    if ticket is None or failures:
        return
    ok("dc1")

    # ---- dc2 — identity binding ------------------------------------------
    planless_identity_check("dc2", proof, ticket, ticket_path, feature_id)

    # ---- dc3 — diff scope: recomputed allowed files, nothing else --------
    recomputed = sorted({c["catalog"] for c in changes})
    if sorted(proof["allowed_files"]) != recomputed:
        fail("dc3", proof_path, "allowed_files does not recompute from the changes list")
    for catalog in recomputed:
        if not catalog.endswith(STRING_CATALOG_SUFFIXES):
            fail("dc3", catalog, "not a string catalog (.strings or .xcstrings)")
        if catalog.startswith("/") or ".." in catalog.split("/"):
            fail("dc3", catalog, "not a repo-relative path")
    permitted = set(recomputed) | {proof_path, ticket_path}
    for line in git("diff", "--name-status", f"{base_sha}..{head_sha}").splitlines():
        parts = line.split("\t")
        status, paths = parts[0], parts[1:]
        for path in paths:
            if path not in permitted:
                fail("dc3", path, "changed outside the declared catalogs (diff-scope guard)")
        if status.startswith(("D", "R")) and any(p in set(recomputed) for p in paths):
            fail("dc3", paths[0], "a declared catalog may only be edited, never deleted or renamed")
    if not failures:
        ok("dc3", f"{len(recomputed)} catalog(s)")

    # ---- dc4 — content match against BOTH trees --------------------------
    for change in changes:
        catalog, key = change["catalog"], change["key"]
        locale = change.get("locale")
        variation = change.get("plural_variation")
        base_value, base_err = catalog_value(git_show_bytes(base_sha, catalog), catalog, key,
                                             locale, variation)
        if change["expected_current"] is None:
            # A plural variation being ADDED: the base tree must not have it.
            if base_value is not None:
                fail("dc4", f"{catalog}:{key}",
                     f"the {variation} plural variation already exists in the base tree — the ticket declared it new")
        elif base_value != change["expected_current"]:
            fail("dc4", f"{catalog}:{key}",
                 f"base tree does not say the expected current text ({base_err or 'value differs'})")
        head_value, head_err = catalog_value(git_show_bytes(head_sha, catalog), catalog, key,
                                             locale, variation)
        if head_value != change["new_value"]:
            fail("dc4", f"{catalog}:{key}",
                 f"head tree does not say the declared new text ({head_err or 'value differs'})")
    if not failures:
        ok("dc4", f"{len(changes)} change(s) match both trees")


def verify_bug_fix(base_sha, head_sha, feature_id, proof, proof_raw,
                   proof_path, ticket_path, plan_path):
    """The planless CONTAINED bug-fix PR (ledger-and-proof spec §6.5,
    purpose bug-fix). No plan and no approvals exist — the proof carries the
    investigation record, the repro-test identifier, and the declared fix
    scope. Unlike a direct change there is no deterministic content check
    (the suite + AI review judge the fix); these checks bound its blast
    radius mechanically:
      bf1 existence + schema (and NO plan file — a contained fix has none)
      bf2 identity binding
      bf3 diff scope — changed paths ⊆ fix scope ∪ test ADDITIONS ∪ the
          proof/ticket files (a modified existing test file fails: tests are
          locked, D92)
    """
    # ---- bf1 — existence + schema + canonical form -----------------------
    ticket = planless_common_checks(
        "bf1", proof, proof_raw, proof_path, plan_path, ticket_path,
        ["feature_id", "purpose", "export_seq", "investigation",
         "repro_test", "fix_scope", "tests_directory"],
        "a contained bug-fix PR must not carry a plan file (over-threshold fixes go through the feature pipeline)")
    fix_scope = proof.get("fix_scope", [])
    if not isinstance(fix_scope, list) or not fix_scope:
        fail("bf1", proof_path, "fix_scope must be a non-empty list (an undeclarable scope fails the plan gate closed — it never ships planless)")
        return
    tests_dir = proof.get("tests_directory", "")
    if not isinstance(tests_dir, str) or not tests_dir or tests_dir.startswith("/") or ".." in tests_dir.split("/"):
        fail("bf1", proof_path, "tests_directory must be a repo-relative directory path")
        return
    if not proof.get("repro_test"):
        fail("bf1", proof_path, "repro_test identifier is empty")
    if ticket is None or failures:
        return
    ok("bf1")

    # ---- bf2 — identity binding ------------------------------------------
    planless_identity_check("bf2", proof, ticket, ticket_path, feature_id)

    # ---- bf3 — diff scope: fix scope ∪ test additions ∪ proof/ticket -----
    # Exactly the proof and ticket files are permitted from the plans dir,
    # matching dc3 — a PR smuggling any other file under plans/<feature_id>/
    # fails, the same blast-radius posture as the direct-change path.
    scope = set(fix_scope)
    for path in scope:
        if path.startswith("/") or ".." in path.split("/"):
            fail("bf3", path, "fix_scope entries must be repo-relative paths")
    tests_prefix = tests_dir if tests_dir.endswith("/") else tests_dir + "/"
    for line in git("diff", "--name-status", f"{base_sha}..{head_sha}").splitlines():
        parts = line.split("\t")
        status, paths = parts[0], parts[1:]
        for path in paths:
            if path in scope or path in (proof_path, ticket_path):
                continue
            if path.startswith(tests_prefix):
                if not status.startswith("A"):
                    fail("bf3", path, "test files may only be ADDED in a bug fix — existing tests are locked (D92)")
                continue
            fail("bf3", path, "changed outside the declared fix scope (diff-scope guard)")
    if not failures:
        ok("bf3", f"{len(scope)} file(s) in scope")


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

    # ---- Governance-only PRs (Coast/the founder ship their own gate
    # updates). The shipped checks and workflows are GOVERNING class: agents
    # cannot write them (the tool wall), so a diff touching NOTHING but
    # governance paths is app/founder maintenance — there is no agent work
    # to prove. Deterministic pass, the same posture as a plans-only diff.
    # A MIXED diff (governance + anything else) takes the full proof path
    # and fails check 6 for the governance files, so agent work can never
    # smuggle a script change alongside itself.
    governance_prefixes = ("Scripts/checks/", ".github/")
    all_changed = [p for p in
                   git("diff", "--name-only", f"{base_sha}..{head_sha}").splitlines() if p]
    if all_changed and all(p.startswith(governance_prefixes) for p in all_changed):
        ok("governance-only", f"{len(all_changed)} governance file(s); no agent work to prove")
        return finish()

    # Identity comes from the PR's CONTENT, never the branch name: the branch
    # format is a per-project setting (branch-name delta, round 23), so the
    # harness derives the feature from the single plans/<feature_id>/
    # directory this PR touches between base and head.
    changed = git("diff", "--name-only", f"{base_sha}..{head_sha}", "--", "plans/")
    ids = sorted({p.split("/")[1] for p in changed.splitlines() if p.count("/") >= 2})
    if len(ids) != 1:
        fail("check2", "plans/", f"expected exactly one plans/<feature_id>/ dir changed base..head, found: {ids or 'none'}")
        return finish()
    feature_id = ids[0]
    plan_path = f"plans/{feature_id}/plan.json"
    proof_path = f"plans/{feature_id}/proof.json"
    ticket_path = f"plans/{feature_id}/ticket.json"

    # ---- Planless direct-change PRs branch on the proof's purpose --------
    # (coast-ticket-types-spec.md §3, D116: no plan, no approvals — the
    # proof carries the ticketed edit and the trees must agree with it.)
    peek_raw = read_head_bytes(proof_path)
    if peek_raw is not None:
        try:
            peek = json.loads(peek_raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            peek = None
        if isinstance(peek, dict) and peek.get("purpose") == "direct-change":
            verify_direct_change(base_sha, head_sha, feature_id, peek, peek_raw,
                                 proof_path, ticket_path, plan_path)
            return finish()
        # A contained bug fix (§6.5, purpose bug-fix) is also planless —
        # bounded by its declared fix scope; AI review still runs.
        if isinstance(peek, dict) and peek.get("purpose") == "bug-fix":
            verify_bug_fix(base_sha, head_sha, feature_id, peek, peek_raw,
                           proof_path, ticket_path, plan_path)
            return finish()

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
        fail("check2", "feature_id", f"proof/plan/PR disagree: {proof['feature_id']}/{plan['feature_id']}/{feature_id}")
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
    # The plan-bar approval (the human's approval of the plan itself, with
    # the cost estimate it was made against). Enforced on IMPLEMENTATION
    # PRs only — a plan PR may legitimately precede the approval event.
    # When the history rides the proof, its operative verdict must approve
    # and must bind THIS plan file's hash — an approval of some earlier
    # revision proves nothing.
    plan_approval = proof.get("plan_approval")
    if plan_approval is not None and purpose == "implementation-pr":
        if not isinstance(plan_approval, list) or not plan_approval \
                or not all(isinstance(v, dict) for v in plan_approval):
            fail("check3", "plan", "plan_approval must be a non-empty list of verdict objects")
        else:
            last = plan_approval[-1]
            if last.get("verdict") != "approved":
                fail("check3", "plan", "plan-bar operative verdict is not approved")
            if last.get("item_content_hash") != proof.get("plan_file_hash"):
                fail("check3", "plan", "plan-bar approval binds a different plan file hash")
            context = last.get("context")
            if not isinstance(context, dict) or "estimate_low_usd_micros" not in context:
                fail("check3", "plan", "plan-bar approval carries no cost estimate")
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
