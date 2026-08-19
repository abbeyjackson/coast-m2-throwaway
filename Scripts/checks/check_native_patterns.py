#!/usr/bin/env python3
"""Coast native-pattern checker — the deterministic escape-hatch gate (D128).

Native platform patterns are mandatory: on a native platform, navigation and
core structure (windows, layout) use native mechanisms, and a non-native
workaround needs explicit human approval on the plan. This check makes that
rule deterministic: it greps the PR diff's ADDED lines for a curated,
per-platform native-escape-hatch signature list and FAILS the PR when a hatch
appears in a file the plan's approved native-deviations list doesn't cover.

Ships in the scaffolded repo under the GOVERNING class (agents cannot touch
it — D12). Pure function of the PR trees + the proof file at head. No
network, no ledger access, no model calls (same posture as verify_proof.py).

The approved list travels with the plan approval: approving the plan writes
`approved_native_deviations` into the plan-bar approval's context, and the
proof export carries it to `plans/<feature_id>/proof.json`. This checker
trusts the OPERATIVE (last, approved) plan-bar verdict only — and the
record's integrity is guarded by verify_proof.py's check 8, which
superset-protects `plan_approval` against the merged predecessor proof
(plans/ is agent-writable; both gates run in the same required workflow, so
an agent commit that drops, replaces, or alters the approval record fails
the PR there before this checker's read could be fooled — a chain-valid
APPENDED forgery is the documented residual until Coast's assembly commit
is SHA-pinned at the merge gate). Planless PRs
(direct changes, contained bug fixes) have no plan approval — for them ANY
listed hatch fails, which IS the rule: an unexplained failure is a reason to
pause and ask, never to iterate on non-native workarounds.

The signature list mirrors the one Swift home
(Sources/CoastOrchestrator/NativePatternSignatures.swift in the Coast
package — the CLDR/verify_proof one-home precedent). The feedback loop: any
workaround the AI domain-rules reviewer catches that isn't listed gets ADDED
to both homes, so the deterministic net grows over time.

Usage: check_native_patterns.py <base_sha> <head_sha>
Run from the repository root of a full-history checkout at <head_sha>.

Exit 0 = pass. Any failure prints a machine-readable line
FAIL native-pattern {file}:{signature_id}: {reason} and exits 1.
"""

import json
import re
import subprocess
import sys
import unicodedata

# Per-platform signature lists, keyed by the file extensions each platform's
# code uses. iOS/SwiftUI ships first (the test vehicle); Android and React
# Native are structurally ready — their lists grow via the feedback loop.
# Each signature: id (stable — approved deviations in merged proofs cite it),
# pattern (regex over each ADDED line), paired (optional second regex that
# must ALSO match some added line in the same file — the hatch is the pair),
# words (plain words for the failure message).
SIGNATURES = {
    "ios": {
        "extensions": (".swift",),
        "list": [
            {"id": "appkit-reach-through",
             "pattern": r"\b(NSWindow|NSApplication|NSApp)\b",
             "words": "raw NSWindow/NSApplication reach-through from SwiftUI — window behavior belongs to SwiftUI's scene and window APIs"},
            {"id": "representable-window-reach",
             "pattern": r"\bNSViewRepresentable\b",
             "paired": r"\.window\b",
             "words": "an NSViewRepresentable touching .window — a bridge view reaching into the hosting window's chrome"},
            {"id": "window-chrome-override",
             "pattern": r"\b(standardWindowButton|styleMask|makeKeyAndOrderFront|titlebarAppearsTransparent)\b",
             "words": "window-chrome override (standardWindowButton/styleMask/makeKeyAndOrderFront/titlebarAppearsTransparent) — replaces the platform's window controls"},
            {"id": "hidden-window-toolbar",
             "pattern": r"\.toolbar\(\s*\.hidden\s*,\s*for:\s*\.windowToolbar\s*\)",
             "words": "hiding the window toolbar (.toolbar(.hidden, for: .windowToolbar)) — removes the native title bar and traffic lights"},
            {"id": "hand-rolled-router",
             "pattern": r"\benum\s+\w*Route\w*\b",
             "words": "a hand-rolled Route enum in place of NavigationStack — navigation belongs to the platform's navigation container"},
            {"id": "scrim-modal",
             "pattern": r"Color\.black\.opacity\(",
             "words": "a full-screen scrim/dimming overlay used as a modal — modals belong to .sheet/.popover/.alert"},
            {"id": "nsevent-key-monitor",
             "pattern": r"NSEvent\s*\.\s*add(Local|Global)MonitorForEvents",
             "words": "an NSEvent key monitor — key handling belongs to the platform's focus and command system"},
            {"id": "focus-key-override",
             "pattern": r"(@FocusState\b|\.focused\()",
             "paired": r"(\.onKeyPress\(|keyDown|NSEvent)",
             "words": "focus APIs used to override key handling — the platform's command/shortcut system owns keys"},
        ],
    },
    "android": {"extensions": (".kt", ".kts"), "list": []},
    "react-native": {"extensions": (".ts", ".tsx", ".js", ".jsx"), "list": []},
}

GOVERNANCE_PREFIXES = ("Scripts/checks/", ".github/")

failures = []


def fail(subject, reason):
    failures.append({"subject": subject, "reason": reason})
    print(f"FAIL native-pattern {subject}: {reason}")


def git(*args, check=True):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def match_form(path):
    """Case- and NFC-insensitive comparison form (mirrors verify_proof.py)."""
    return unicodedata.normalize("NFC", path).lower()


def target_covers(target, path):
    """Exact match, or a '/**' glob covering the path (mirrors the plan
    item target rules — F3 §4.3)."""
    t, p = match_form(target), match_form(path)
    if t.endswith("/**"):
        prefix = t[:-2]  # keep the trailing "/"
        return p.startswith(prefix) or p == prefix[:-1]
    return t == p


def added_lines(base_sha, head_sha, path):
    # A renamed file surfaces whole (the pathspec-limited diff can't pair
    # old->new), so renaming a file with a previously approved hatch fails
    # until the deviation names the NEW path. Deliberately fail-closed:
    # approvals name files.
    diff = git("diff", f"{base_sha}..{head_sha}", "--unified=0", "--", path)
    return [line[1:] for line in diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")]


def pattern_matches(pattern, lines, joined):
    """Per-line match, OR a match against the file's added lines joined with
    whitespace stripped — a hatch wrapped in ordinary chained-modifier style
    (`Color.black` newline `.opacity(0.4)`) is still the hatch."""
    return (any(re.search(pattern, line) for line in lines)
            or re.search(pattern, joined) is not None)


def signature_hits(lines, signatures):
    """The signature ids whose pattern (and paired pattern, when the hatch is
    the pair) match the file's added lines."""
    joined = "".join(line.strip() for line in lines)
    hits = []
    for signature in signatures:
        if not pattern_matches(signature["pattern"], lines, joined):
            continue
        paired = signature.get("paired")
        if paired and not pattern_matches(paired, lines, joined):
            continue
        hits.append(signature)
    return hits


def approved_deviations(head_sha, changed_paths):
    """The plan's approved native deviations, read from the proof file at PR
    head: the plan-bar approval's operative verdict carries them in context
    (approving the plan wrote them there; the proof export brought them
    here). No proof, no plan approval, or a non-approved operative verdict
    => no deviations are approved."""
    ids = sorted({p.split("/")[1] for p in changed_paths
                  if p.startswith("plans/") and p.count("/") >= 2})
    if len(ids) != 1:
        return []
    raw = subprocess.run(["git", "show", f"{head_sha}:plans/{ids[0]}/proof.json"],
                         capture_output=True)
    if raw.returncode != 0:
        return []
    try:
        proof = json.loads(raw.stdout.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return []
    plan_approval = proof.get("plan_approval")
    if not isinstance(plan_approval, list) or not plan_approval:
        return []
    operative = plan_approval[-1]
    if not isinstance(operative, dict) or operative.get("verdict") != "approved":
        return []
    entries = operative.get("context", {}).get("approved_native_deviations", [])
    return [e for e in entries if isinstance(e, dict)
            and isinstance(e.get("file"), str)
            and isinstance(e.get("signatures"), list)]


def main():
    if len(sys.argv) != 3:
        print("usage: check_native_patterns.py <base_sha> <head_sha>")
        return 2
    base_sha, head_sha = sys.argv[1], sys.argv[2]

    changed = []
    for line in git("diff", "--name-status", f"{base_sha}..{head_sha}").splitlines():
        parts = line.split("\t")
        status = parts[0]
        if status == "D":
            continue  # a deleted file adds no lines
        changed.append(parts[-1])

    # Governance-only diffs are the app's/founder's own gate maintenance —
    # same deterministic posture as the proof verifier's governance lane.
    if changed and all(p.startswith(GOVERNANCE_PREFIXES) for p in changed):
        print("PASS native-pattern (governance-only diff)")
        return finish()

    deviations = None  # loaded lazily — most PRs add no hatches
    for path in changed:
        # Test targets are exempt (SPM convention: Tests/) — the rule guards
        # the app's shipped structure; tests exercising an approved hatch
        # shouldn't each need their own deviation entry.
        if path.startswith("Tests/"):
            continue
        for platform in SIGNATURES.values():
            if not path.endswith(platform["extensions"]) or not platform["list"]:
                continue
            lines = added_lines(base_sha, head_sha, path)
            for signature in signature_hits(lines, platform["list"]):
                if deviations is None:
                    deviations = approved_deviations(head_sha, changed)
                covered = any(target_covers(entry["file"], path)
                              and signature["id"] in entry["signatures"]
                              for entry in deviations)
                if not covered:
                    fail(f"{path}:{signature['id']}",
                         signature["words"]
                         + " — not covered by an approved native deviation on the plan (D128: "
                           "a non-native workaround for navigation or core structure needs "
                           "explicit approval; never chase an unexplained failure with hacks — "
                           "pause and ask)")

    if not failures:
        print("PASS native-pattern")
    return finish()


def finish():
    if failures:
        print(json.dumps({"result": "fail", "failures": failures}))
        return 1
    print(json.dumps({"result": "pass"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
