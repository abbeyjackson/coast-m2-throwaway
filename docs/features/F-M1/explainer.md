# Greeter — How This Works

## What it does
Greeter is a small piece of the app that says hello. Give it a name, and it
replies with a friendly greeting. Don't give it a name, and it falls back to
a generic "Hello, world!" greeting.

## Examples
- Ask it to greet "Ada" → it replies "Hello, Ada!"
- Ask it to greet with no name given → it replies "Hello, world!"
- Ask it to greet an empty name → it still replies, just with nothing after
  the comma: "Hello, !"

## Why it matters
This is a foundational building block — other parts of the app can use
Greeter whenever they need to produce a friendly greeting message, without
having to reimplement the wording themselves.

## Status
Implemented and covered by automated tests that check the exact wording of
each greeting.
