import XCTest
@testable import Greeter

/// Additional unit tests locking behavior below the plan's resolution
/// that the requirement tests (GreeterTests) don't already pin: internal
/// boundaries where a plausible-but-wrong implementation could regress.
final class GreeterBoundaryTests: XCTestCase {
    /// A naive implementation might sanitize, trim, or escape special
    /// characters in the name before interpolating it. This locks that
    /// the name is passed through verbatim.
    func testGreetWithSpecialCharactersPassesNameThroughUnmodified() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "O'Brien \"Ace\""), "Hello, O'Brien \"Ace\"!")
    }

    /// Greeter holds no mutable state, so repeated calls (with the same
    /// or no arguments) must always produce the same result. This guards
    /// against a regression that introduces hidden state or randomness.
    func testGreetIsPureAcrossRepeatedCalls() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(), greeter.greet())
        XCTAssertEqual(greeter.greet(name: "Ada"), greeter.greet(name: "Ada"))
    }
}
