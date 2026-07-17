#!/usr/bin/env python3
"""Coast review agents — literal GitHub PR reviewers (D26), running in the
isolated CI runner (D47) with the customer's model key from Actions secrets.

CI-side agent shape per the tool-authority matrix §8: read the PR checkout
and diff, judge the work against the approved plan, and submit a real PR
review — the reviewer decides blocking vs non-blocking. It cannot push
(workflow token: contents read, pull-requests write); the pusher credential
never enters CI.

Three review passes ride this job, sharing one shape — only the
instructions differ (F2 §8):

1. the general review agent (M1),
2. the Test-review specialist (D62, M2) — judges test QUALITY; the D92
   locked-tests rule means it reviews tests, never edits them,
3. the Domain-rules reviewer (D64, M2) — judges compliance with the
   project's domain-rules document.

Two invariants keep the one-identity model sound:

- All passes post as the one reviewer App identity, and GitHub lets a
  user's later state-bearing review supersede their earlier one. So the
  general pass alone carries APPROVE (and posts first), and specialist
  passes post COMMENT when clean and REQUEST_CHANGES only on a blocking
  finding — a clean pass can never dissolve a standing block.
- Verdicts are collected from ALL passes before ANY review is posted. A
  failed run therefore posts nothing (exactly the M1 atomicity), so Coast's
  harness-crash classifier (failed gate-review job + no CHANGES_REQUESTED
  review = infra, re-run) stays sound and a crashed run can never leave a
  standing APPROVE for work the specialists Never reviewed.

Reviewers use the thin model client (D44/D90): a direct Messages API call,
structured output validated field-by-field with bounded retries (D37/D72).
Everything a finding cites is mechanically verified to exist (D39).

Usage: review_agent.py <pr_number> <base_sha> <head_sha>
Env: ANTHROPIC_API_KEY (Actions secret), GH_TOKEN, GITHUB_REPOSITORY.
"""

import json
import os
import subprocess
import sys
import urllib.request

MODEL = "claude-sonnet-5"
RETRY_FIELD = 3  # D72
MAX_DIFF_CHARS = 60_000
MAX_TEST_FILE_CHARS = 20_000
MAX_TEST_SECTIONS_TOTAL_CHARS = 120_000
DOMAIN_RULES_DOC = "docs/domain-rules.md"  # D64; input registered in engine-required-inputs.md


def sh(*args, stdin=None):
    result = subprocess.run(args, capture_output=True, text=True, input=stdin)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:3])}… failed: {result.stderr.strip()}")
    return result.stdout


def call_model(system, messages):
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({
            "model": MODEL,
            "max_tokens": 4096,
            "system": system,
            "messages": messages,
        }).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
        })
    with urllib.request.urlopen(request, timeout=300) as response:
        payload = json.load(response)
    return "".join(block.get("text", "") for block in payload.get("content", []))


FINDINGS_SHAPE = """"summary": "<one paragraph>",
 "findings": [{"file": "<path you may cite>", "line": <int, optional>,
               "rule": "<what principle>", "finding": "<specific, actionable>",
               "blocking": true|false}]}
Rules: verdict "request_changes" requires at least one blocking finding; every finding
cites file/line/rule (D39) and its "file" must be a path you were shown (the diff, or a
document handed to you); a clean pass still lists what you checked in "summary" (a bare
verdict is invalid)."""

# The general pass carries the PR's one state-bearing approval, and Coast's
# gate waits for APPROVED or CHANGES_REQUESTED — so "comment" is not a legal
# general verdict (non-blocking observations are non-blocking findings on an
# approve).
GENERAL_SHAPE = """Reply with ONLY a JSON object, no markdown fence, of the shape:
{"verdict": "approve" | "request_changes",
 """ + FINDINGS_SHAPE

SPECIALIST_SHAPE = """Reply with ONLY a JSON object, no markdown fence, of the shape:
{"verdict": "approve" | "request_changes" | "comment",
 """ + FINDINGS_SHAPE


GENERAL_SYSTEM = """You are Coast's review agent: a literal GitHub pull-request reviewer for an
orchestrated build system. The deterministic facts are settled before you read anything:
the proof file verified, every diff path inside the declared scope, deletions matched to
approved removals, build and tests green. Do NOT re-derive those. Your judgment residue:

- Does the implementation honor the approved plan items' semantics (right kind of thing,
  right place, faithful to each item's description)?
- Do the tests genuinely lock the acceptance criteria (real assertions, not
  false-passing)?
- Is the below-plan-resolution elaboration sound (no smuggled scope, no speculative
  abstraction, honest naming)?

You decide blocking vs non-blocking, exactly like a human reviewer. """ + GENERAL_SHAPE


TEST_REVIEW_SYSTEM = """You are Coast's Test-review specialist (D62): a literal GitHub pull-request
reviewer who judges TEST QUALITY only. Coding agents author their own tests, and tests
are locked once written (D92) — you are the judgment net that closes that gap. You
review tests; you never edit them. Build/test results are settled facts: everything in
this PR already passes. Passing is not your question; whether passing MEANS anything is.

Judge only the tests in the diff:

- Do the requirement tests genuinely lock the plan's acceptance criteria — a real
  Given-When-Then exercised with real assertions on real output?
- False-passing patterns: tautologies (asserting a value against itself or a constant
  copied from the implementation), asserting only that no error was thrown, testing a
  stub or mock instead of the behavior, assertions so weak any implementation passes.
- Negative and edge coverage honesty: do tests that claim to assert rejection of bad
  input actually assert the rejection (D64's negative-coverage concern)?
- Post-work unit tests (D24): do they add coverage below plan resolution, or merely
  restate the requirement tests?

Do not judge implementation design, naming, or architecture — the general review agent
owns those. A finding outside test quality is out of your scope; leave it out. You
decide blocking vs non-blocking. """ + SPECIALIST_SHAPE


DOMAIN_RULES_SYSTEM = """You are Coast's Domain-rules reviewer (D64): a literal GitHub pull-request
reviewer who judges DOMAIN-RULE COMPLIANCE only. The project's business invariants live
in one authoritative place — the domain-rules document — and your job is to check the
diff against exactly those rules, never rules you invent. Build/test results and scope
checks are settled facts; do not re-derive them.

- When a domain-rules document is provided: check each rule that the diff could touch,
  and cite the specific rule in each finding (the document itself is a citable file).
- A diff that touches no rule's territory is a clean pass — say which rules you
  considered.
- When NO domain-rules document exists yet: state that plainly in your summary, judge
  only against invariants the plan itself establishes (its item descriptions and
  acceptance criteria), and never manufacture a rule. Absence of the document is a
  fact to report, not a finding against this PR.

Do not judge test quality or implementation design — other reviewers own those. You
decide blocking vs non-blocking. """ + SPECIALIST_SHAPE


def validate_review(candidate, citable_paths, allowed_verdicts):
    """Field-level validation (D37/D39): returns the list of field errors.
    Defensive about shape — schema-legal-but-wrong JSON (a list, string
    findings) must come back as a field rejection, never a crash."""
    if not isinstance(candidate, dict):
        return ["response: must be a single JSON object of the required shape"]
    errors = []
    if candidate.get("verdict") not in allowed_verdicts:
        errors.append("verdict: must be " + " | ".join(allowed_verdicts))
    if not candidate.get("summary"):
        errors.append("summary: required, non-empty (a bare verdict is invalid)")
    findings = candidate.get("findings", [])
    if not isinstance(findings, list):
        errors.append("findings: must be an array of finding objects")
        findings = []
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            errors.append(f"findings[{index}]: must be an object with file/rule/finding/blocking")
            continue
        if finding.get("file") not in citable_paths:
            errors.append(f"findings[{index}].file: '{finding.get('file')}' is not a path you were shown "
                          "(everything cited must exist — mechanical check)")
        if "line" in finding and not isinstance(finding.get("line"), int):
            errors.append(f"findings[{index}].line: must be an integer when present")
        if not finding.get("finding"):
            errors.append(f"findings[{index}].finding: required")
    if candidate.get("verdict") == "request_changes" \
            and not any(isinstance(f, dict) and f.get("blocking") for f in findings):
        errors.append("verdict request_changes requires at least one blocking finding")
    return errors


def run_pass(name, system, user_prompt, citable_paths, allowed_verdicts):
    """One review pass: bounded surgical field-rejection rounds (D37/D72).
    Returns the validated review dict, or None after exhaustion."""
    messages = [{"role": "user", "content": user_prompt}]
    for attempt in range(1, RETRY_FIELD + 1):
        text = call_model(system, messages).strip()
        try:
            candidate = json.loads(text)
            errors = validate_review(candidate, citable_paths, allowed_verdicts)
        except ValueError as err:
            errors = [f"not valid JSON: {err}"]
            candidate = None
        if not errors:
            return candidate
        messages += [{"role": "assistant", "content": text},
                     {"role": "user", "content": "RETRY_FIELD — invalid fields: " + " | ".join(errors)
                      + ". Resubmit the full JSON with ONLY these corrected."}]
        print(f"{name}: field rejection round {attempt}: {errors}")
    return None


def read_capped(path, cap):
    """Read a checkout file for prompt context; binary/undecodable bytes are
    replaced rather than crashing the job (a fixture under Tests/ must never
    take the review down).

    Symlink rule (F2 §3.1's rule, applied CI-side): never read through a
    symlink, and the resolved path must stay inside the checkout. The diff's
    paths are agent-authored — a symlink to /proc/self/environ under a tests/
    path would otherwise pull this job's secrets into a model prompt whose
    output is posted publicly."""
    if os.path.islink(path):
        return "[skipped: symlink — reviews never read through links]"
    real = os.path.realpath(path)
    workspace = os.path.realpath(os.getcwd())
    if not real.startswith(workspace + os.sep):
        return "[skipped: resolves outside the checkout]"
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read(cap + 1)
    except OSError as err:
        return f"[unreadable: {err}]"
    if len(content) > cap:
        content = content[:cap] + "\n… [truncated]"
    return content


def post_review(repo, pr_number, event, review, label):
    lines = [f"**{label}** ({MODEL})", "", review["summary"], ""]
    for finding in review.get("findings", []):
        marker = "🛑 blocking" if finding.get("blocking") else "💬 non-blocking"
        where = f"`{finding['file']}`" + (f":{finding['line']}" if "line" in finding else "")
        lines.append(f"- {marker} — {where} — {finding.get('rule', '')}: {finding['finding']}")
    body = "\n".join(lines)
    sh("gh", "api", "-X", "POST", f"/repos/{repo}/pulls/{pr_number}/reviews",
       "-f", f"event={event}", "-f", f"body={body}")
    print(f"{label}: review submitted: {event}")


def main():
    pr_number, base_sha, head_sha = sys.argv[1], sys.argv[2], sys.argv[3]
    repo = os.environ["GITHUB_REPOSITORY"]

    feature_id = os.environ.get("GITHUB_HEAD_REF", "").removeprefix("feature/")
    plan = open(f"plans/{feature_id}/plan.json").read()
    diff = sh("git", "diff", f"{base_sha}..{head_sha}")
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n… [diff truncated]"
    # NUL-separated so a path containing spaces stays one path — the
    # file-in-diff check must never reject a finding over a legal filename.
    diff_paths = set(p for p in
                     sh("git", "diff", "--name-only", "-z", f"{base_sha}..{head_sha}").split("\0") if p)

    base_prompt = (f"The approved plan (already merged via its own reviewed PR):\n{plan}\n\n"
                   f"The implementation diff to review:\n{diff}")

    # The Test-review specialist gets the changed test files in full: judging
    # assertion quality needs the tests themselves, not just hunks. ("Tests/"
    # anywhere in the path — SPM convention; genesis binds the real layout.)
    # Total size is capped too: a PR with thousands of tiny test files must
    # inflate neither the customer's model bill nor the prompt past the API
    # limit (a deterministic crash loop).
    test_sections = []
    test_section_total = 0
    for path in sorted(diff_paths):
        if "tests/" not in path.lower() or not os.path.exists(path):
            continue
        if test_section_total >= MAX_TEST_SECTIONS_TOTAL_CHARS:
            test_sections.append(f"… [more changed test files omitted — total size cap reached: {path} and beyond]")
            break
        section = f"--- {path} (full content at head) ---\n" + read_capped(path, MAX_TEST_FILE_CHARS)
        test_sections.append(section)
        test_section_total += len(section)
    test_prompt = base_prompt + ("\n\nThe changed test files in full:\n" + "\n".join(test_sections)
                                 if test_sections else
                                 "\n\nNo test files changed in this diff.")

    # The Domain-rules reviewer gets the document, and may cite it (D39's
    # existence check extends to exactly what it was handed).
    domain_citable = set(diff_paths)
    if os.path.exists(DOMAIN_RULES_DOC):
        rules_doc = (f"The project's domain-rules document ({DOMAIN_RULES_DOC}):\n"
                     + read_capped(DOMAIN_RULES_DOC, MAX_DIFF_CHARS))
        domain_citable.add(DOMAIN_RULES_DOC)
    else:
        rules_doc = (f"No domain-rules document exists for this project yet ({DOMAIN_RULES_DOC} is absent). "
                     "Judge only against invariants the plan itself establishes, and say so in your summary.")

    # Collect every verdict BEFORE posting anything (atomic like M1): a
    # failed run posts no reviews, so it can never leave a standing APPROVE
    # for work the specialists never judged, and Coast's crash classifier
    # (failed job + no CHANGES_REQUESTED = infra) stays sound.
    passes = [
        ("Coast review agent", GENERAL_SYSTEM, base_prompt, diff_paths,
         ("approve", "request_changes")),
        ("Coast Test-review specialist", TEST_REVIEW_SYSTEM, test_prompt, diff_paths,
         ("approve", "request_changes", "comment")),
        ("Coast Domain-rules reviewer", DOMAIN_RULES_SYSTEM, base_prompt + "\n\n" + rules_doc,
         domain_citable, ("approve", "request_changes", "comment")),
    ]
    collected = []
    for label, system, prompt, citable, allowed in passes:
        review = run_pass(label, system, prompt, citable, allowed)
        if review is None:
            print(f"{label}: failed structured output after retries — failing the job "
                  "with NO reviews posted (blocked, never silent)")
            return 1
        collected.append((label, review))

    # Post: the general pass first (the one state-bearing APPROVE), then the
    # specialists — REQUEST_CHANGES on blocking findings, else COMMENT, never
    # APPROVE (a later same-identity APPROVE would supersede a standing block).
    for index, (label, review) in enumerate(collected):
        if index == 0:
            event = {"approve": "APPROVE", "request_changes": "REQUEST_CHANGES"}[review["verdict"]]
        else:
            event = "REQUEST_CHANGES" if review["verdict"] == "request_changes" else "COMMENT"
        post_review(repo, pr_number, event, review, label)

    # A blocking review leaves the PR unmergeable via the ruleset — the fix
    # loop (L4) is Coast's to drive; the job itself succeeded.
    return 0


if __name__ == "__main__":
    sys.exit(main())
