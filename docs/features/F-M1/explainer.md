# F-M1: Greeter — How This Works

## What it does
This feature adds a simple "Greeter" that can say hello.

- If you tell it a name, it says: **"Hello, <name>!"** (for example, "Hello, Alice!")
- If you don't tell it a name, it says: **"Hello, world!"**
- If you give it an empty name, it says: **"Hello, !"**

## Why it matters
This is the foundational building block for the app — a small, well-tested
piece of functionality that proves the pipeline (writing code, testing it,
and shipping it) works end-to-end. Everything else builds on this same
pattern.

## How it's built
- The `Greeter` is a small, public piece of code anyone else in the app can
  use to produce a greeting.
- It has two ways to ask for a greeting: one where you give it a name, and
  one where you don't (which just says hello to "world").
- A set of automated tests locks in exactly what each of these should
  produce, so if anyone changes this code in the future in a way that
  breaks the expected behavior, the tests will catch it immediately.

## What "done" looks like
All four requirement tests pass:
1. Greeting Alice by name returns "Hello, Alice!"
2. Greeting with an empty name returns "Hello, !"
3. Greeting with no name given returns "Hello, world!"
4. The Greeter and its greeting methods are accessible from outside the
   module (proving it's usable by the rest of the app).
