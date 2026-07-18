import XCTest
@testable import Greeter

/// Locks internal boundaries of `Greeter.greet` that the requirement tests
/// don't pin: statelessness across calls, and that the name is interpolated
/// verbatim with no trimming or sanitization.
final class GreeterBoundaryTests: XCTestCase {
    func testGreetIsStatelessAcrossCallsOnSameInstance() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada"), "Hello, Ada!")
        XCTAssertEqual(greeter.greet(name: "Grace"), "Hello, Grace!")
        XCTAssertEqual(greeter.greet(), "Hello, world!")
    }

    func testGreetDoesNotTrimWhitespaceInName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "  Ada  "), "Hello,   Ada  !")
    }

    func testGreetInterpolatesNameVerbatimWithoutSanitization() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "O'Brien 🎉"), "Hello, O'Brien 🎉!")
    }
}
