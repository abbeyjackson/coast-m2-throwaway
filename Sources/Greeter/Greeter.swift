/// Produces greeting strings for a given name.
public struct Greeter {
    public init() {}

    /// Returns a greeting for the given name.
    public func greet(name: String) -> String {
        "Hello, \(name)!"
    }

    /// Returns a default greeting.
    public func greet() -> String {
        "Hello, world!"
    }
}
