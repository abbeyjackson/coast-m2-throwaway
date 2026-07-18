import XCTest
@testable import Greeter

final class GreeterTests: XCTestCase {
    func testGreetWithNameReturnsPersonalizedGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ava"), "Hello, Ava!")
    }

    func testGreetWithNoArgumentsReturnsWorldGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(), "Hello, world!")
    }

    func testGreetWithEmptyNameReturnsEmptyGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: ""), "Hello, !")
    }
}
