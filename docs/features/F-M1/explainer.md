# F-M1: Greeter — How This Works

**What it does:** This feature adds a simple "Greeter" that can say hello.

- If you give it a name (like "Ada"), it replies: **"Hello, Ada!"**
- If you don't give it a name, it replies: **"Hello, world!"**

**Why it matters:** This is the foundational building block for the app — a
tiny, well-tested piece of functionality that proves the pipeline (writing
code, testing it, and shipping it) works end-to-end. Future features will
build on the same pattern.

**How it's checked:** Two automated tests confirm the behavior:
1. Asking for a greeting with a name returns the personalized message.
2. Asking for a greeting with no name returns the default "Hello, world!"
   message.

Both tests currently pass, meaning the Greeter behaves exactly as intended.
