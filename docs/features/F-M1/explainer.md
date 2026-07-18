# Greeter — how this works

Greeter is a tiny building block that produces a friendly greeting message.

- If you give it a name, it says: "Hello, `<name>`!" (e.g. "Hello, Ada!")
- If you give it an empty name, it says: "Hello, !"
- If you don't give it a name at all, it says: "Hello, world!"

There's no complicated logic here — it just plugs your name into a fixed
greeting sentence. This is a foundational piece other parts of the app can
use whenever they need to say hello to a user by name.
