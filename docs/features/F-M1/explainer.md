# F-M1: Greeter

## What this is

`Greeter` is a small, self-contained service with one job: say hello.
It's the very first "walking skeleton" feature built through the Coast
pipeline, meant to prove the whole system works end-to-end rather than
to do anything complicated.

## What it does

- If you give it a name, it says a personalized hello:
  - "Ada" → "Hello, Ada!"
  - "" (an empty name) → "Hello, !"
- If you don't give it a name at all, it says a generic hello:
  - "Hello, world!"

## How you'd use it

Anywhere in the codebase, you can create a `Greeter` and ask it for a
greeting:

```swift
let greeter = Greeter()
greeter.greet(name: "Ada")   // "Hello, Ada!"
greeter.greet()              // "Hello, world!"
```

## Why it matters

Even though the behavior is simple, this feature exercises the full
Coast loop: a plan item, a locked requirement test that fails first,
an implementation that makes it pass, and this explainer describing
the result in plain language. Everything built later follows the same
shape.
