/// A simple, stateless formatter that produces greeting strings.
public struct Greeter {
    /// Creates a new greeter.
    public init() {}

    /// Formats a greeting addressed to the given name.
    ///
    /// - Parameter name: The name to include in the greeting.
    /// - Returns: A greeting string in the form "Hello, <name>!".
    public func greet(name: String) -> String {
        "Hello, \(name)!"
    }

    /// Formats a generic greeting.
    ///
    /// - Returns: The greeting string "Hello, world!".
    public func greet() -> String {
        "Hello, world!"
    }

    /// Formats a farewell addressed to the given name.
    ///
    /// - Parameter name: The name to include in the farewell.
    /// - Returns: A farewell string in the form "Goodbye, <name>!".
    public func farewell(name: String) -> String {
        // TODO: placeholder stub, not yet implemented
        ""
    }

    /// Formats a generic farewell.
    ///
    /// - Returns: The farewell string "Goodbye!".
    public func farewell() -> String {
        // TODO: placeholder stub, not yet implemented
        ""
    }
}
