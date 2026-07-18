import XCTest
@testable import Greeter

/// Requirement tests locking the acceptance criteria for the `Greeter`
/// service (F-M1). These must fail against the current placeholder
/// implementation and pass once `Greeter.greet` is implemented for real.
final class GreeterTests: XCTestCase {
    func testGreetWithNameReturnsPersonalizedGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada"), "Hello, Ada!")
    }

    func testGreetWithNoArgumentsReturnsWorldGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(), "Hello, world!")
    }

    func testGreetWithEmptyStringNameReturnsEmptyGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: ""), "Hello, !")
    }
}
