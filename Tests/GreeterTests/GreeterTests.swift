import XCTest
@testable import Greeter

/// Requirement tests locking the acceptance criteria for the public
/// `Greeter` type. These must fail until Greeter.swift is implemented.
final class GreeterTests: XCTestCase {
    func testGreetWithNameReturnsPersonalizedGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada"), "Hello, Ada!")
    }

    func testGreetWithNoArgumentsReturnsWorldGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(), "Hello, world!")
    }
}
