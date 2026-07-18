# F-M1: Greeter

## What this is

A small piece of code called `Greeter` that says hello. Give it a name, and
it greets that person by name. Don't give it a name, and it greets the
whole world instead.

## How it works

- Ask the Greeter to say hello to "Ada" and it replies: `Hello, Ada!`
- Ask the Greeter to say hello with no name at all and it replies:
  `Hello, world!`
- Even an empty name still gets a polite reply: `Hello, !`

## Why it matters

This is the simplest possible building block: a predictable, tested way to
produce a greeting message. Other parts of the app can rely on it always
behaving the same way, which is confirmed by automated tests that run
every time the code changes.
