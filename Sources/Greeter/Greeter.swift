/// Public greeting type (stub — real logic arrives via the Coast pipeline).
public struct Greeter {
    public init() {}

    public func greet(name: String) -> String {
        "Hello, \(name)!"
    }

    public func greet() -> String {
        "Hello, world!"
    }
}
