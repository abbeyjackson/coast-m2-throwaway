import XCTest
@testable import Greeter

final class GreeterTests: XCTestCase {
    func testGreetWithNameReturnsPersonalizedGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada"), "Hello, Ada!")
    }

    func testGreetWithNoArgumentsReturnsDefaultGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(), "Hello, world!")
    }

    func testGreetWithEmptyStringNameReturnsEmptyGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: ""), "Hello, !")
    }
}
