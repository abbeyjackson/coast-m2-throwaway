import XCTest
@testable import Greeter

/// Post-work unit tests (D24): edge cases and internal behavior below the
/// plan's resolution that the requirement tests do not cover. These are
/// not new requirements — they exercise `Greeter` more thoroughly to guard
/// against regressions in string handling.
final class GreeterEdgeCaseTests: XCTestCase {

    // GIVEN a Greeter instance WHEN greet(name:) is called with a name
    // containing only whitespace THEN the whitespace is preserved verbatim
    // in the output (no trimming).
    func testGreetWithWhitespaceOnlyName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "   "), "Hello,    !")
    }

    // GIVEN a Greeter instance WHEN greet(name:) is called with a name
    // containing leading/trailing whitespace THEN the whitespace is
    // preserved verbatim (no trimming).
    func testGreetWithLeadingAndTrailingWhitespaceName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "  Bob  "), "Hello,   Bob  !")
    }

    // GIVEN a Greeter instance WHEN greet(name:) is called with a name
    // containing special/punctuation characters THEN they are embedded
    // verbatim, unescaped.
    func testGreetWithSpecialCharactersInName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "O'Brien-Smith, Jr."), "Hello, O'Brien-Smith, Jr.!")
    }

    // GIVEN a Greeter instance WHEN greet(name:) is called with a name
    // containing Unicode characters (accents, non-Latin scripts, emoji)
    // THEN they are embedded verbatim.
    func testGreetWithUnicodeName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "José 日本語 🎉"), "Hello, José 日本語 🎉!")
    }

    // GIVEN a Greeter instance WHEN greet(name:) is called with a name
    // containing an embedded newline THEN the newline is preserved
    // verbatim rather than stripped or escaped.
    func testGreetWithEmbeddedNewlineInName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Line1\nLine2"), "Hello, Line1\nLine2!")
    }

    // GIVEN a Greeter instance WHEN greet(name:) is called with a very
    // long name THEN the full name is included in the result without
    // truncation.
    func testGreetWithVeryLongName() {
        let greeter = Greeter()
        let longName = String(repeating: "a", count: 10_000)
        XCTAssertEqual(greeter.greet(name: longName), "Hello, \(longName)!")
    }

    // GIVEN a Greeter instance WHEN greet(name:) is called repeatedly with
    // the same name THEN it returns the same result each time (pure,
    // stateless behavior — no hidden mutable state).
    func testGreetIsPureAndRepeatable() {
        let greeter = Greeter()
        let first = greeter.greet(name: "Repeatable")
        let second = greeter.greet(name: "Repeatable")
        XCTAssertEqual(first, second)
    }

    // GIVEN two independently constructed Greeter instances WHEN each
    // calls greet() with no arguments THEN both return the identical
    // default greeting, confirming no shared or instance-specific state
    // influences the default.
    func testMultipleGreeterInstancesShareNoState() {
        let first = Greeter()
        let second = Greeter()
        XCTAssertEqual(first.greet(), second.greet())
    }

    // GIVEN a Greeter instance WHEN greet(name:) is called with a name that
    // itself contains the literal substring "Hello, " and "!" THEN the
    // output is a straightforward concatenation with no double-processing
    // or recursive substitution.
    func testGreetWithNameContainingGreetingLikeSubstring() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Hello, world!"), "Hello, Hello, world!!")
    }
}
