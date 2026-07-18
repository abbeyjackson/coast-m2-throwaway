import XCTest
@testable import Greeter

final class GreeterBoundaryTests: XCTestCase {
    /// Locks that the greeting does not trim whitespace-only names, distinguishing
    /// "no name provided" (a separate empty-string case) from "a name that happens
    /// to be blank" — the implementation must not special-case or normalize input.
    func testGreetWithWhitespaceOnlyNameIsNotTrimmed() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "  "), "Hello,   !")
    }
}
