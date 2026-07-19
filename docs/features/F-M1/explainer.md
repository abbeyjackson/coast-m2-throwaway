# F-M1: Greeter

## What this does

This feature adds a small `Greeter` tool that says hello.

- If you give it a name, like "Ada", it replies: "Hello, Ada!"
- If you don't give it a name, it replies: "Hello, world!"
- If you give it an empty name, it still replies politely: "Hello, !"

## Why it matters

It's a simple, well-tested building block that other parts of the
app can use whenever they need to greet a user by name (or greet
generically when no name is available).

## How it works

The `Greeter` type has two ways to ask for a greeting:

1. `greet(name:)` — pass in a name, get back a personalized greeting.
2. `greet()` — no name needed, get back a generic greeting.

There's no complex logic here — just straightforward, predictable
text formatting, backed by automated tests that check each case.
