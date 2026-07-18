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

    func testGreeterExposesExpectedPublicAPI() {
        let greeter = Greeter()
        let named: (String) -> String = greeter.greet(name:)
        let unnamed: () -> String = greeter.greet
        XCTAssertEqual(named("Ada"), "Hello, Ada!")
        XCTAssertEqual(unnamed(), "Hello, world!")
    }
}
