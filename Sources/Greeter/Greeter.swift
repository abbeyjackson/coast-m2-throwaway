/// A minimal greeting service (see docs/features/F-M1/explainer.md).
///
/// `Greeter` produces friendly, personalized greetings when given a name,
/// and falls back to a generic "world" greeting when no name is given.
public struct Greeter {
    public init() {}

    /// Returns a personalized greeting for the given `name`, e.g. "Hello, Ada!".
    /// An empty string produces "Hello, !".
    public func greet(name: String) -> String {
        "Hello, \(name)!"
    }

    /// Returns the default greeting, "Hello, world!".
    public func greet() -> String {
        "Hello, world!"
    }
}
