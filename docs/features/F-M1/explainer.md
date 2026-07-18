# Greeter — How This Works

## What it does
The `Greeter` is a small piece of code that says hello. Give it a name, and
it will greet that name. Don't give it a name, and it will greet "world"
instead.

## Examples
- Ask it to greet "Ada" → it replies "Hello, Ada!"
- Ask it to greet with no name at all → it replies "Hello, world!"
- Ask it to greet an empty name → it replies "Hello, !"

## Why it matters
This is a simple building block used to confirm that greetings work
correctly before more features are built on top of it.

## Note on the generated class diagram
`docs/diagrams/Greeter-classes.md` also lists `GreeterModule`. That is not
part of this feature — it's the pre-existing scaffold namespace marker
(`Sources/Greeter/GreeterModule.swift`, an empty `enum` predating this PR,
still exercised by `Tests/GreeterTests/ScaffoldTests.swift`). The diagram is
generated from the whole `Greeter` module, not just this diff, so it
correctly shows both types. `Greeter.swift` itself defines only the
`Greeter` struct described above.
