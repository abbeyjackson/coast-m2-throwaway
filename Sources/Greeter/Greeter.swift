/// Public greeting type.
public struct Greeter {
    public init() {}

    /// Returns a personalized greeting for the given name.
    public func greet(name: String) -> String {
        "Hello, \(name)!"
    }

    /// Returns the default greeting.
    public func greet() -> String {
        "Hello, world!"
    }
}
