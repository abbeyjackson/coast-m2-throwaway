# F-M1: Greeter — How This Works

**What it does:** Greeter is a small piece of the app that says hello. Give it
a name, and it politely greets that person. Don't give it a name, and it
falls back to a friendly generic greeting.

**In plain terms:**
- Ask it to greet "Ada" → it replies "Hello, Ada!"
- Ask it to greet nobody in particular → it replies "Hello, world!"
- Ask it to greet an empty name → it still replies, just with nothing where
  the name would go: "Hello, !"

**Why it matters:** This is the simplest possible building block — a single,
predictable greeting behavior — that other parts of the app can rely on and
build personalized messages on top of later.

**What was built:** One public type, `Greeter`, with two ways to ask for a
greeting: one that takes a name, and one that doesn't. Both always return the
same kind of message shape ("Hello, ...!"), so behavior is consistent and
easy to test.
