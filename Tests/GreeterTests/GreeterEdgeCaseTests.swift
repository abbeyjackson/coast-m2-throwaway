import XCTest
@testable import Greeter

/// Post-work unit tests (D24) covering edge cases and internal behavior of
/// `Greeter.greet(name:)` that fall below the plan's acceptance-criteria
/// resolution. These exercise unusual input the requirement tests
/// (GreeterTests.swift) don't cover, but do not change or duplicate them.
final class GreeterEdgeCaseTests: XCTestCase {
    func testGreetWithWhitespaceOnlyNameIsPassedThroughUnmodified() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "   "), "Hello,    !")
    }

    func testGreetWithLeadingAndTrailingWhitespaceIsNotTrimmed() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "  Ada  "), "Hello,   Ada  !")
    }

    func testGreetWithUnicodeNameIsPreserved() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Grace 👩‍💻"), "Hello, Grace 👩‍💻!")
    }

    func testGreetWithNonLatinScriptNameIsPreserved() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "田中"), "Hello, 田中!")
    }

    func testGreetWithNameContainingPunctuationIsNotEscaped() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "O'Brien"), "Hello, O'Brien!")
    }

    func testGreetWithNameContainingDoubleQuotesIsNotEscaped() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "\"Ada\""), "Hello, \"Ada\"!")
    }

    func testGreetWithNameContainingNewlineIsPreservedVerbatim() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada\nLovelace"), "Hello, Ada\nLovelace!")
    }

    func testGreetWithNameContainingExclamationMarkDoesNotDuplicatePunctuation() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada!"), "Hello, Ada!!")
    }

    func testGreetWithVeryLongNameIsHandledWithoutTruncation() {
        let greeter = Greeter()
        let longName = String(repeating: "a", count: 10_000)
        XCTAssertEqual(greeter.greet(name: longName), "Hello, \(longName)!")
    }

    func testGreetWithNameEqualToWorldDoesNotCollideWithDefaultGreeting() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "world"), "Hello, world!")
        XCTAssertEqual(greeter.greet(name: "world"), greeter.greet())
    }

    func testGreetIsPure_RepeatedCallsWithSameNameReturnSameResult() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada"), greeter.greet(name: "Ada"))
    }

    func testGreetWithNoArgumentsIsConsistentAcrossMultipleInstances() {
        XCTAssertEqual(Greeter().greet(), Greeter().greet())
    }
}
