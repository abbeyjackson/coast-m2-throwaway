# Project rules

This file ships with your project as a curated default, sourced from
established, widely used engineering and safety guides (listed under Sources
at the bottom). **It belongs to you.** Edit any rule, delete what doesn't
apply to your product, and add your own rules on top — you never have to
write a document like this from scratch. Automated reviewers check every
code change against exactly the rules in this file, so a rule you add here
is enforced on every change from then on.

How to read a rule: each one has an id (used in reviews, tickets, and
tests), a single checkable statement, and the guide it comes from in
brackets. Keep new rules checkable — a reviewer must be able to answer
"does this change break the rule — yes or no?"

## Money and payments (PAY)

- **PAY-1** Money amounts are stored and calculated with decimal or
  whole-number types — never binary floating-point types (`Float`,
  `Double`), which cannot represent cents exactly. [Industry-wide practice;
  see Sources]
- **PAY-2** Every stored money amount carries its currency. Amounts in
  different currencies are never added or compared without an explicit
  conversion step. [Industry-wide practice]
- **PAY-3** Rounding is decided once (which method, at which step) and every
  total is computed in one place and reused — never recomputed slightly
  differently in two places. [Industry-wide practice]
- **PAY-4** Digital goods and features sold inside the app go through the
  platform's in-app purchase system. [Apple App Review Guidelines §3.1]
- **PAY-5** Raw card numbers never touch the app's own code or storage —
  payment collection goes through a certified payment provider's SDK or the
  platform's payment sheet. [PCI DSS scope rules; OWASP]

## Security (SEC)

- **SEC-1** All network traffic uses encrypted connections (HTTPS/TLS).
  No plaintext HTTP endpoints. [OWASP ASVS; OWASP MASVS-NETWORK]
- **SEC-2** Data arriving from outside the app — user input, network
  responses, deep links, shared files — is validated before use, and
  database queries are parameterized, never assembled from strings.
  [OWASP ASVS; OWASP Cheat Sheets: Input Validation, Query Parameterization]
- **SEC-3** No home-made cryptography. Encryption, hashing, and random
  generation use the platform or standard library implementations.
  [OWASP MASVS-CRYPTO]
- **SEC-4** Secrets — API keys, tokens, credentials — never appear in
  source code, logs, analytics, or error messages. [OWASP ASVS; MASVS-STORAGE]
- **SEC-5** Error messages shown to users never expose internals such as
  stack traces, query text, or file paths. [OWASP Cheat Sheet: Error Handling]

## Accounts and sign-in (AUTH)

- **AUTH-1** Sign-in uses the platform's sign-in system or an established
  identity provider — never a hand-rolled account store. If passwords must
  be stored, they are hashed with a current memory-hard algorithm
  (Argon2id, scrypt, or bcrypt), never encrypted or kept readable.
  [OWASP Cheat Sheets: Authentication, Password Storage]
- **AUTH-2** Session tokens expire, can be revoked, and are regenerated at
  sign-in and at any privilege change. [OWASP Cheat Sheet: Session Management]
- **AUTH-3** Sign-in attempts are rate-limited so accounts can't be
  brute-forced. [OWASP ASVS]
- **AUTH-4** Sensitive actions — deleting the account, changing email,
  password, or payment details — re-confirm the user's identity first.
  [OWASP ASVS]

## Privacy and personal data (PRIV)

- **PRIV-1** The app collects only the data the feature in front of the
  user actually needs. [Apple App Review Guidelines §5.1; GDPR data-minimization principle]
- **PRIV-2** Every kind of data the app collects or shares is declared in
  the store's privacy listing — no undeclared collection. [Apple App Review Guidelines §5.1]
- **PRIV-3** Personal data never appears in logs, analytics events, crash
  reports, or URLs. [OWASP MASVS-STORAGE; OWASP Cheat Sheet: Logging]
- **PRIV-4** Users can delete their account, and the personal data behind
  it, from inside the app. [Apple App Review Guidelines §5.1.1(v)]
- **PRIV-5** Personal data stored on the device lives in the app's
  protected container with the platform's data protection applied — never
  in world-readable locations. [OWASP MASVS-STORAGE]

## Accessibility (ACC)

- **ACC-1** Text has a contrast ratio of at least 4.5:1 against its
  background (3:1 for large text). [WCAG 2.2 — 1.4.3]
- **ACC-2** Tap/click targets are at least 44×44 points per platform
  guidance, and never smaller than 24×24 pixels. [Apple HIG; WCAG 2.2 — 2.5.8]
- **ACC-3** Every interactive element has a screen-reader label that says
  what it does. [WCAG 2.2 — 4.1.2; Apple HIG Accessibility]
- **ACC-4** Text respects the system text-size setting (Dynamic Type on
  Apple platforms) without truncating away meaning. [Apple HIG; WCAG 2.2 — 1.4.4]
- **ACC-5** Color is never the only signal — errors, success, and selection
  are also conveyed by text, shape, or icon. [WCAG 2.2 — 1.4.1]

## User-generated content (UGC) — applies only if users can post content others see

- **UGC-1** There is a way to report content, block users, and filter
  objectionable material. [Apple App Review Guidelines §1.2]
- **UGC-2** Uploaded content is checked for expected type and size before
  it is processed or stored. [OWASP Cheat Sheet: File Upload]

## Engineering quality (ENG)

- **ENG-1** Reactive state: any state that can change while it is
  displayed, or that outlives a single function call, is published through
  the platform's observation system (Observation/Combine on Apple
  platforms) — never polled, never manually refreshed. One-shot values stay
  plain: no observation ceremony around constants. [Platform best practice — Apple]
- **ENG-2** Responsive layout: screens adapt using the platform's standard
  layout system — window-size changes on desktop and web, rotation and
  size-class changes on phones and tablets. No fixed screen dimensions.
  [Platform best practice — Apple HIG Layout]
- **ENG-3** Never block a thread: long waits — network calls, spawned
  processes, timers, polling — are asynchronous. No sleeping on a held
  thread, and nothing that blocks is callable from the UI. [Platform best practice — Apple]
- **ENG-4** Child-process lifetime: any process or worker the app spawns is
  tied to its parent's lifetime — quitting the app or cancelling the task
  cleans it up. No orphaned processes. [Platform best practice]
- **ENG-5** No crash on bad input: invalid input or unexpected data
  produces a typed, surfaced error — never a process crash. Assertions that
  halt the app are reserved for programmer errors, not recoverable
  conditions. [Platform best practice; OWASP Cheat Sheet: Error Handling]
- **ENG-6** Secrets live in the platform's secure store — Keychain on Apple
  platforms, Keystore on Android — never in plaintext files, source code,
  or logs. [OWASP MASVS-STORAGE; Apple platform security]

## Tests (TEST)

- **TEST-1** Every acceptance criterion has at least one automated test,
  and each test states which acceptance criterion it verifies. [Project rule]
- **TEST-2** Tests that gate a merge run without live external services —
  external dependencies are faked locally. Tests against live services run
  separately and never block a merge. [Project rule; Google Testing Blog: hermetic testing]
- **TEST-3** A test proves behavior: it fails when the behavior it names is
  broken. Assertions so weak that any implementation passes don't count as
  coverage. [Project rule]

## Documentation (DOC)

- **DOC-1** Every public type and function carries a doc comment saying
  what it does — including parameters and return value where they aren't
  obvious. The generated API reference is built from these. [Project rule]
- **DOC-2** A doc comment must match what the code actually does. A doc
  that reads wrong is treated as a code problem, not a wording problem.
  [Project rule]

---

## Sources

The rules above are written in this project's own words; the guides they
are sourced from (for provenance and further reading):

- **OWASP Application Security Verification Standard (ASVS) 5.0** —
  <https://owasp.org/www-project-application-security-verification-standard/> (CC BY-SA 4.0)
- **OWASP Mobile Application Security Verification Standard (MASVS) 2.1** —
  <https://mas.owasp.org/MASVS/> (CC BY-SA 4.0)
- **OWASP Cheat Sheet Series** — <https://cheatsheetseries.owasp.org/> (CC BY-SA 4.0)
- **W3C Web Content Accessibility Guidelines (WCAG) 2.2** —
  <https://www.w3.org/TR/WCAG22/> (W3C document license; also ISO/IEC 40500)
- **Apple App Review Guidelines** —
  <https://developer.apple.com/app-store/review/guidelines/> (proprietary — referenced only, no text reproduced)
- **Apple Human Interface Guidelines** —
  <https://developer.apple.com/design/human-interface-guidelines/> (proprietary — referenced only)

No text from these guides is reproduced here — every rule is an original
plain-language statement citing its source — so editing or replacing this
file carries no license obligations for you.
