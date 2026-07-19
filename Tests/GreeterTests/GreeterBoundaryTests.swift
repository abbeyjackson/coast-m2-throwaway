import XCTest
@testable import Greeter

/// Locks boundary behavior of Greeter not already pinned by GreeterTests:
/// that the name is passed through untouched (no trimming/sanitizing) and
/// that non-ASCII input is handled correctly.
final class GreeterBoundaryTests: XCTestCase {
    func testGreetPreservesWhitespaceInName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "  Ada  "), "Hello,   Ada  !")
    }

    func testGreetWithUnicodeName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "日本語"), "Hello, 日本語!")
    }
}
