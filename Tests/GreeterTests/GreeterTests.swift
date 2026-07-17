import XCTest
@testable import Greeter

/// Requirement tests locking the acceptance criteria for `Greeter`.
final class GreeterTests: XCTestCase {

    // GIVEN a Greeter instance WHEN greet(name:) is called with "Alice"
    // THEN it returns "Hello, Alice!"
    func testGreetWithNameAlice() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Alice"), "Hello, Alice!")
    }

    // GIVEN a Greeter instance WHEN greet(name:) is called with an empty
    // string "" THEN it returns "Hello, !"
    func testGreetWithEmptyName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: ""), "Hello, !")
    }

    // GIVEN a Greeter instance WHEN greet() is called with no arguments
    // THEN it returns "Hello, world!"
    func testGreetWithNoArguments() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(), "Hello, world!")
    }

    // GIVEN the Greeter type WHEN it is referenced from a test target via
    // @testable import Greeter THEN Greeter and both greet methods are
    // public and accessible.
    func testGreeterAndGreetMethodsArePublicAndAccessible() {
        let greeter: Greeter = Greeter()
        let withName: String = greeter.greet(name: "Accessibility")
        let noArgs: String = greeter.greet()
        // Accessibility alone is proven by compilation across the module
        // boundary; the requirement is only locked once the accessible
        // methods also produce the specified results.
        XCTAssertEqual(withName, "Hello, Accessibility!")
        XCTAssertEqual(noArgs, "Hello, world!")
    }
}
