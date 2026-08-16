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
   project's domain-rules document. When the document does not exist yet,
   this pass posts a deterministic COMMENT stating the absence — no model
   call (its residual judgment would duplicate the general pass).

Cost shape: the plan + diff ride as one shared, cache_control-marked system
block, byte-identical across passes and retry rounds — billed at full input
price once, then read from the prompt cache (cost benchmark follow-up,
2026-07-17).

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

Reviewers use the thin model client (D44/D90): one direct API call per
pass, structured output validated field-by-field with bounded retries
(D37/D72). Everything a finding cites is mechanically verified to exist
(D39).

Multi-provider (M5 H38, D150): the model, provider, and effort come from
the frozen registration snapshot's `ci_reviews` pick, which Coast writes
into `plans/<feature_id>/ticket.json` as `{"model", "provider", "effort"}`
— the registry table lives in Coast, never duplicated here. Three
providers, two client shapes:

- "anthropic": the Messages API (existing), effort via `output_config.
  effort` (verified against platform.claude.com, 2026-08-15).
- "openai" and "gemini": one OpenAI-shaped chat-completions caller —
  OpenAI's own API and Gemini's official OpenAI-compatible endpoint
  (https://generativelanguage.googleapis.com/v1beta/openai/, Google's
  documented surface) differ only in base URL and key. Effort via
  `reasoning_effort` (both providers document it; verified 2026-08-15).
  Prompt caching is automatic on both (no cache_control field exists in
  this shape); cached-prefix reads surface in usage as
  prompt_tokens_details.cached_tokens.

Effort is ALWAYS sent explicitly (D152: never inherit a provider's own
default — their defaults are tuned for capability, not for someone else's
money).

Local-model projects (M5 H40, D151): a repo with NO key secret reviews on
the founder's Mac — Coast runs the same passes there and posts them
through the customer-owned reviewer App. This job then verifies that
review exists for the exact head SHA (deterministic, free) instead of
reviewing here; it stays blocking until the review lands.

Usage: review_agent.py <pr_number> <base_sha> <head_sha>
Env: ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY (Actions secrets;
only the frozen pick's provider is required — none at all means verify),
REVIEWER_APP_SLUG (the verify identity), GH_TOKEN, GITHUB_REPOSITORY.
"""

import json
import os
import subprocess
import sys
import urllib.request

# The one shipped FALLBACK row (not a table): what a ticket with no
# frozen pick reviews on — the same model and effort Coast's registry
# ships as its review default (Sonnet at high; explicit high is
# documented as identical to the provider's default behavior, so pre-H38
# tickets review exactly as before).
DEFAULT_REVIEW = {"model": "claude-sonnet-5", "provider": "anthropic", "effort": "high"}

# Key env var and (for the OpenAI shape) base URL per provider.
PROVIDER_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}
OPENAI_SHAPE_BASE = {
    "openai": "https://api.openai.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
}
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


def load_review_pick(feature_id):
    """The frozen ci_reviews pick from the ticket container. The
    shipped-default fallback covers only a ticket that carries NO pick
    (pre-H38 tickets) — and says so in the log, never silently. A pick
    that IS present but unusable (a legacy plain string, or model-only)
    normalizes to a model-only dict, which require_provider_key refuses
    in plain words — a review must never silently run on a different
    brain than the one the ticket froze."""
    try:
        ticket = json.load(open(f"plans/{feature_id}/ticket.json"))
    except (OSError, ValueError) as err:
        print(f"ci_reviews pick unreadable ({err}) — reviewing on the shipped default "
              f"{DEFAULT_REVIEW['model']}", flush=True)
        return dict(DEFAULT_REVIEW)
    pick = ticket.get("ci_reviews")
    if isinstance(pick, str) and pick.strip():
        return {"model": pick}
    if not isinstance(pick, dict) or not pick.get("model"):
        print(f"no ci_reviews pick on this ticket — reviewing on the shipped default "
              f"{DEFAULT_REVIEW['model']}", flush=True)
        return dict(DEFAULT_REVIEW)
    return pick


def provider_key(pick):
    """The picked provider's key secret, or None (unknown provider, or the
    secret is absent). The caller decides what None means: with an
    Anthropic key on the repo it is a configuration mistake (plain-words
    refusal via require_provider_key); with NO key at all it is the
    local-review shape (M5 H40) and CI verifies instead of reviewing."""
    provider = pick.get("provider")
    if provider not in PROVIDER_KEY_ENV:
        return None
    return os.environ.get(PROVIDER_KEY_ENV[provider], "").strip() or None


def require_provider_key(pick):
    """The plain-words refusals for a repo that DOES review in CI (some key
    exists) but can't run this ticket's pick. A model frozen without a
    provider (a name Coast's registry didn't know) is refused too — a
    review must never silently run on a different brain than the one this
    ticket froze."""
    provider = pick.get("provider")
    if provider not in PROVIDER_KEY_ENV:
        raise SystemExit(
            f"The AI review can't run: this ticket asks for the model \"{pick.get('model')}\" "
            "but doesn't say which company runs it. Pick a review brain from the list in "
            "Coast's settings and resubmit the ticket.")
    env = PROVIDER_KEY_ENV[provider]
    raise SystemExit(
        f"The AI review can't run: this repository has no {env} secret, and this "
        f"ticket's reviews are set to run on {provider}. Add that key to the project "
        "in Coast to turn these reviews on.")


# ---- The local-review verify (M5 H40, D151) ----------------------------
# A project building on a local model has NO key secret: the review passes
# run on the founder's Mac and post through the customer-owned reviewer
# App. This job then VERIFIES — deterministically, free, via the GH API
# with its existing reviewer token — that such a review exists for the
# CURRENT head SHA. Enforcement never weakens: no review yet = the check
# fails in plain words, and unreviewed code cannot merge.

def local_review_verdict(reviews, head_sha, expected_login):
    """Pure verify rule (tested by Scripts/dev/review_verify_smoke.py): a
    STATE-BEARING review (APPROVED or CHANGES_REQUESTED — the general
    pass always posts one) by the reviewer App, submitted for EXACTLY the
    current head. A review on a stale head never counts (the same
    current-head-only rule Coast's own classifier uses). When the
    workflow doesn't hand the App's login, any App bot user counts —
    only Apps can hold this repo's review vote."""
    for review in reviews:
        if not isinstance(review, dict):
            continue
        if review.get("commit_id") != head_sha:
            continue
        if review.get("state") not in ("APPROVED", "CHANGES_REQUESTED"):
            continue
        login = (review.get("user") or {}).get("login", "")
        if expected_login:
            if login == expected_login:
                return True
        elif login.endswith("[bot]"):
            return True
    return False


def paged_reviews(repo, pr_number):
    """Every review on the PR, page-walked explicitly. GitHub's default
    page is 30 and three passes plus fix rounds overflow it, so the newest
    state-bearing review would otherwise fall off the end — and `gh api
    --paginate` emits one JSON array PER PAGE, which is not parseable as a
    single document. Same walk the app's own reads use."""
    reviews = []
    page = 1
    while True:
        raw = sh("gh", "api",
                 f"/repos/{repo}/pulls/{pr_number}/reviews?per_page=100&page={page}")
        batch = json.loads(raw or "[]")
        if not isinstance(batch, list):
            break
        reviews += batch
        if len(batch) < 100:
            break
        page += 1
    return reviews


def verify_local_review(repo, pr_number, head_sha):
    """The verify step's body: pass when the Mac's review is on this exact
    head, fail with plain words when none is yet."""
    slug = os.environ.get("REVIEWER_APP_SLUG", "").strip()
    expected = f"{slug}[bot]" if slug else None
    if local_review_verdict(paged_reviews(repo, pr_number), head_sha, expected):
        print("This repository has no model key, so its reviews run on the founder's Mac: "
              f"a review from the reviewer App is on this exact commit ({head_sha[:8]}) — verified.",
              flush=True)
        return 0
    # Both honest cases in one message: the Mac hasn't posted yet, or this
    # project never had a local model to review with.
    raise SystemExit(
        "No review is on this exact commit yet. This repository has no model key, so its "
        "reviews run on the founder's Mac — start Coast and it will run them. If this "
        "project doesn't build on a local model, add a model key to it in Coast and the "
        "reviews will run here instead.")


def call_model(system_blocks, messages, pick, key):
    """One review call on the frozen pick's provider. system_blocks is a
    list of Anthropic-style content blocks; the FIRST block carries the
    shared review context, byte-identical across all passes and retry
    rounds, so every provider's prompt cache serves it after the first
    call (Anthropic: the cache_control breakpoint below; OpenAI and
    Gemini: automatic prefix caching on their OpenAI-shaped surface).
    Effort is sent explicitly on every call (D152)."""
    if pick["provider"] == "anthropic":
        body = {
            "model": pick["model"],
            "max_tokens": 4096,
            "system": system_blocks,
            "messages": messages,
        }
        if pick.get("effort"):
            body["output_config"] = {"effort": pick["effort"]}
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            })
        with urllib.request.urlopen(request, timeout=300) as response:
            payload = json.load(response)
        usage = payload.get("usage", {})
        meter(pick["model"],
              usage.get("input_tokens", 0), usage.get("output_tokens", 0),
              usage.get("cache_read_input_tokens", 0),
              usage.get("cache_creation_input_tokens", 0))
        return "".join(block.get("text", "") for block in payload.get("content", []))

    # The OpenAI shape (OpenAI itself, and Gemini's official OpenAI-
    # compatible endpoint). System blocks flatten to one system message —
    # this shape has no cache_control field. max_completion_tokens bounds
    # reasoning AND visible output together (OpenAI's documented
    # semantics), so it carries headroom well past the answer's size: at
    # reasoning_effort "high" a tight cap would spend the whole budget
    # thinking and return an empty answer.
    body = {
        "model": pick["model"],
        "max_completion_tokens": 16384,
        "messages": [{"role": "system",
                      "content": "\n\n".join(block["text"] for block in system_blocks)}]
                    + messages,
    }
    if pick.get("effort"):
        body["reasoning_effort"] = pick["effort"]
    request = urllib.request.Request(
        OPENAI_SHAPE_BASE[pick["provider"]] + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {key}",
        })
    with urllib.request.urlopen(request, timeout=300) as response:
        payload = json.load(response)
    usage = payload.get("usage", {})
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    # prompt_tokens_details.cached_tokens is OpenAI's documented usage
    # field for automatically-cached prefixes; a provider that omits it
    # (or answers 0) meters everything as uncached input — conservative,
    # never an undercount. No cache-write surcharge exists in this shape,
    # so cache_creation stays 0.
    meter(pick["model"],
          usage.get("prompt_tokens", 0) - cached, usage.get("completion_tokens", 0),
          cached, 0)
    choices = payload.get("choices", [])
    if not choices:
        return ""
    return choices[0].get("message", {}).get("content") or ""


def meter(model, input_tokens, output_tokens, cache_read, cache_write):
    # Metering line for the job log: reviewer calls run here on the customer's
    # key, outside the sidecar's cost stream, so this is where they're counted
    # (CostGuard ingests these at S14 and prices them per model).
    print(f"COAST-REVIEW-USAGE model={model}"
          f" input_tokens={input_tokens}"
          f" output_tokens={output_tokens}"
          f" cache_read_input_tokens={cache_read}"
          f" cache_creation_input_tokens={cache_write}",
          flush=True)


FINDINGS_SHAPE = """"summary": "<one paragraph>",
 "findings": [{"file": "<path you may cite>", "line": <int, optional>,
               "rule": "<what principle>", "finding": "<specific, actionable>",
               "blocking": true|false}]}
Rules: verdict "request_changes" requires at least one blocking finding; every finding
cites file/line/rule (D39) and its "file" must be a path you were shown (the diff, or a
document handed to you); a clean pass still lists what you checked in "summary" (a bare
verdict is invalid).
Summary discipline: the summary is an audit line, not an essay — one clause per
rule/criterion you actually checked, plus at most one sentence of overall judgment. Its
length follows the work reviewed, never a target: a trivial diff earns a sentence; a
large one earns exactly as many clauses as it has things checked. No filler, no
restating the diff, no praise prose. Findings likewise: the issue and the fix, nothing
more."""

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
- Redundant volume: tests that re-exercise an already-pinned code path with cosmetic
  input variations add noise, not coverage — flag it (non-blocking) so the suite stays
  a statement of behavior, not bulk.

Do not judge implementation design, naming, or architecture — the general review agent
owns those. A finding outside test quality is out of your scope; leave it out. You
decide blocking vs non-blocking. """ + SPECIALIST_SHAPE


DOMAIN_RULES_SYSTEM = """You are Coast's Domain-rules reviewer (D64): a literal GitHub pull-request
reviewer who judges DOMAIN-RULE COMPLIANCE only. The project's business invariants live
in one authoritative place — the domain-rules document — and your job is to check the
diff against exactly those rules, never rules you invent. Build/test results and scope
checks are settled facts; do not re-derive them.

- Check each rule that the diff could touch, and cite the specific rule in each
  finding (the document itself is a citable file). Never manufacture a rule the
  document does not state.
- A diff that touches no rule's territory is a clean pass — say which rules you
  considered.

(You run only when the document exists — an absent document is handled
deterministically by the harness, without a model call.)

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


def run_pass(name, system_blocks, user_prompt, citable_paths, allowed_verdicts, pick, key):
    """One review pass: bounded surgical field-rejection rounds (D37/D72).
    Returns the validated review dict, or None after exhaustion."""
    messages = [{"role": "user", "content": user_prompt}]
    for attempt in range(1, RETRY_FIELD + 1):
        text = call_model(system_blocks, messages, pick, key).strip()
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


def post_review(repo, pr_number, event, review, label, engine):
    """engine names what produced the review — the model for a model pass, or
    "deterministic — no model call" for the harness's own verdicts."""
    lines = [f"**{label}** ({engine})", "", review["summary"], ""]
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

    # Identity from the PR's content, never the branch name (the branch
    # format is a per-project setting — round 23): the feature is the single
    # plans/<feature_id>/ directory this PR touches between base and head.
    changed = sh("git", "diff", "--name-only", f"{base_sha}..{head_sha}", "--", "plans/")
    ids = sorted({p.split("/")[1] for p in changed.splitlines() if p.count("/") >= 2})
    if len(ids) != 1:
        raise SystemExit(f"expected exactly one plans/<feature_id>/ dir changed base..head, found: {ids or 'none'}")
    feature_id = ids[0]

    # Direct-change PRs (coast-ticket-types-spec.md §3, D116): nothing
    # judgeable — the change IS the specification, and verify_proof.py's
    # dc-checks are the gate (diff scope + content match on both trees).
    # The required approving review is submitted deterministically; no
    # model is called and nothing is billed.
    try:
        proof = json.load(open(f"plans/{feature_id}/proof.json"))
    except (OSError, ValueError):
        proof = {}
    if proof.get("purpose") == "direct-change":
        post_review(repo, pr_number, "APPROVE",
                    {"summary": "Direct change: the exact ticketed edit, applied deterministically. "
                                "The proof verifier confirmed the diff touches only the declared "
                                "catalogs and both trees match the declaration — nothing for an AI "
                                "reviewer to judge, so no model was called.",
                     "findings": []},
                    "Direct-change review", "deterministic — no model call")
        # No COAST-REVIEW-USAGE line: nothing was metered, nothing to ingest.
        return
    # The model passes run on the ticket's frozen ci_reviews pick (M5 H38),
    # and the pick's provider key must exist before anything is spent.
    # Without it, two honest shapes (M5 H40): a repo that DOES hold an
    # Anthropic key is misconfigured for this pick — fail in plain words;
    # a repo with NO key at all is the local-review shape — the review ran
    # on the founder's Mac, so VERIFY it exists for this exact head
    # instead of reviewing here (deterministic, free, still blocking).
    pick = load_review_pick(feature_id)
    key = provider_key(pick)
    if key is None:
        if os.environ.get("ANTHROPIC_API_KEY", "").strip():
            require_provider_key(pick)  # raises with the configuration fix
        return verify_local_review(repo, pr_number, head_sha)

    # A contained bug fix (purpose bug-fix, §6.5) has no plan — its context
    # is the investigation record + repro test from the proof; the review
    # judges the fix against those the way a feature review judges the plan.
    if proof.get("purpose") == "bug-fix":
        plan_label = "The bug's investigation record and repro test (no plan exists — a contained fix)"
        plan = json.dumps({"investigation": proof.get("investigation"),
                           "repro_test": proof.get("repro_test"),
                           "fix_scope": proof.get("fix_scope")}, indent=2, ensure_ascii=False)
    else:
        plan_label = "The approved plan (already merged via its own reviewed PR)"
        plan = open(f"plans/{feature_id}/plan.json").read()
    diff = sh("git", "diff", f"{base_sha}..{head_sha}")
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n… [diff truncated]"
    # NUL-separated so a path containing spaces stays one path — the
    # file-in-diff check must never reject a finding over a legal filename.
    diff_paths = set(p for p in
                     sh("git", "diff", "--name-only", "-z", f"{base_sha}..{head_sha}").split("\0") if p)

    # The shared review context is one block, byte-identical for every pass,
    # carried as the FIRST system block with cache_control (see call_model):
    # the plan + diff are billed at full input price once, then read from
    # cache by the later passes and by every retry round. Pass-specific
    # material (test files, the domain-rules document) rides in the user turn,
    # after the cache breakpoint.
    shared_context = {
        "type": "text",
        "text": (f"{plan_label}:\n{plan}\n\n"
                 f"The implementation diff to review:\n{diff}"),
        "cache_control": {"type": "ephemeral"},
    }

    def pass_system(role_system):
        return [shared_context, {"type": "text", "text": role_system}]

    base_prompt = "Review the plan and diff in your system context."

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

    # The generated API reference for each module the diff touches (deltas
    # 31b): the general pass reads it so a doc that reads wrong against the
    # code surfaces as a finding. The pages are Coast-generated world-state
    # in the checkout (docs/api/<Module>-reference.md), capped like tests.
    docs_sections = []
    touched_modules = sorted({p.split("/")[1] for p in diff_paths
                              if p.startswith("Sources/") and p.count("/") >= 2})
    for module in touched_modules:
        page = f"docs/api/{module}-reference.md"
        if not os.path.exists(page):
            continue
        docs_sections.append(f"--- {page} (generated API reference) ---\n"
                             + read_capped(page, MAX_TEST_FILE_CHARS))
    general_prompt = base_prompt + (
        "\n\nThe generated API reference for the modules this diff touches "
        "(these pages are regenerated from the code — flag any that read "
        "wrong or misleading against the diff):\n" + "\n".join(docs_sections)
        if docs_sections else "")

    # Collect every verdict BEFORE posting anything (atomic like M1): a
    # failed run posts no reviews, so it can never leave a standing APPROVE
    # for work the specialists never judged, and Coast's crash classifier
    # (failed job + no CHANGES_REQUESTED = infra) stays sound.
    passes = [
        ("Coast review agent", GENERAL_SYSTEM, general_prompt, diff_paths,
         ("approve", "request_changes")),
        ("Coast Test-review specialist", TEST_REVIEW_SYSTEM, test_prompt, diff_paths,
         ("approve", "request_changes", "comment")),
    ]
    # The Domain-rules pass costs a model call only when there are rules to
    # judge against. With no document, its residual judgment ("invariants the
    # plan itself establishes") duplicates the general pass — so the harness
    # states the absence deterministically instead of paying a model to.
    domain_label = "Coast Domain-rules reviewer"
    engine_by_label = {}  # label -> engine name; absent = the pick's model (a model pass)
    if os.path.exists(DOMAIN_RULES_DOC):
        # The reviewer gets the document, and may cite it (D39's existence
        # check extends to exactly what it was handed).
        domain_citable = set(diff_paths) | {DOMAIN_RULES_DOC}
        rules_doc = (f"The project's domain-rules document ({DOMAIN_RULES_DOC}):\n"
                     + read_capped(DOMAIN_RULES_DOC, MAX_DIFF_CHARS))
        passes.append((domain_label, DOMAIN_RULES_SYSTEM, base_prompt + "\n\n" + rules_doc,
                       domain_citable, ("approve", "request_changes", "comment")))

    collected = []
    for label, system, prompt, citable, allowed in passes:
        review = run_pass(label, pass_system(system), prompt, citable, allowed, pick, key)
        if review is None:
            print(f"{label}: failed structured output after retries — failing the job "
                  "with NO reviews posted (blocked, never silent)")
            return 1
        collected.append((label, review))

    if not os.path.exists(DOMAIN_RULES_DOC):
        label, review = domain_label, {
            "verdict": "comment",
            "summary": (f"No domain-rules document exists for this project yet ({DOMAIN_RULES_DOC} "
                        "is absent), so there are no filed rules to judge this diff against. "
                        "Plan-established invariants are already judged by the general review "
                        "pass. This pass activates automatically once the document exists."),
            "findings": [],
        }
        engine_by_label[label] = "deterministic — no model call"
        collected.append((label, review))

    # Post: the general pass first (the one state-bearing APPROVE), then the
    # specialists — REQUEST_CHANGES on blocking findings, else COMMENT, never
    # APPROVE (a later same-identity APPROVE would supersede a standing block).
    for index, (label, review) in enumerate(collected):
        if index == 0:
            event = {"approve": "APPROVE", "request_changes": "REQUEST_CHANGES"}[review["verdict"]]
        else:
            event = "REQUEST_CHANGES" if review["verdict"] == "request_changes" else "COMMENT"
        post_review(repo, pr_number, event, review, label,
                    engine_by_label.get(label, pick["model"]))

    # A blocking review leaves the PR unmergeable via the ruleset — the fix
    # loop (L4) is Coast's to drive; the job itself succeeded.
    return 0


if __name__ == "__main__":
    sys.exit(main())
