# Farewell Messages

## What this does

The Greeter now knows how to say goodbye, not just hello.

- If you tell it a name, it replies: **"Goodbye, `<name>`!"** (for example, "Goodbye, Abbey!")
- If you don't give it a name, it replies: **"Goodbye!"**

## Why it matters

This gives the app a friendly way to close out an interaction, matching the
existing greeting feature. Anywhere the app already says hello to a user by
name, it can now also say a proper goodbye.

## How it works (in plain terms)

The Greeter is a small helper that produces text messages. It already had a
`greet()` method that says "Hello, world!". We added two matching `farewell`
methods:

1. `farewell(name:)` – takes a name and returns a personalized goodbye.
2. `farewell()` – takes no input and returns a generic goodbye.

No other behavior changed; this is purely additive.
