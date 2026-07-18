import XCTest
@testable import Greeter

/// Covers edge cases and internal behavior of Greeter.greet(...) that fall
/// below the plan's acceptance-criteria resolution (whitespace, unicode,
/// special characters, long input, and instance independence).
final class GreeterEdgeCaseTests: XCTestCase {
    func testGreetWithWhitespaceOnlyNamePreservesWhitespace() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "   "), "Hello,    !")
    }

    func testGreetWithLeadingAndTrailingWhitespaceIsNotTrimmed() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "  Ada  "), "Hello,   Ada  !")
    }

    func testGreetWithUnicodeNameIsPreserved() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "日本語"), "Hello, 日本語!")
    }

    func testGreetWithEmojiNameIsPreserved() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "🎉"), "Hello, 🎉!")
    }

    func testGreetWithSpecialCharactersIsNotEscaped() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "O'Brien & Sons \"Ltd\""), "Hello, O'Brien & Sons \"Ltd\"!")
    }

    func testGreetWithEmbeddedNewlineIsPreserved() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada\nLovelace"), "Hello, Ada\nLovelace!")
    }

    func testGreetWithVeryLongNameDoesNotTruncate() {
        let longName = String(repeating: "a", count: 10_000)
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: longName), "Hello, \(longName)!")
    }

    func testGreetWithNameLiterallyWorldStillPersonalizes() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "world"), "Hello, world!")
    }

    func testGreetIsDeterministicAcrossRepeatedCalls() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada"), greeter.greet(name: "Ada"))
    }

    func testGreetWithNoArgumentsIsDeterministicAcrossInstances() {
        let first = Greeter()
        let second = Greeter()
        XCTAssertEqual(first.greet(), second.greet())
    }

    func testMultipleGreeterInstancesAreIndependent() {
        let first = Greeter()
        let second = Greeter()
        XCTAssertEqual(first.greet(name: "Ada"), "Hello, Ada!")
        XCTAssertEqual(second.greet(name: "Grace"), "Hello, Grace!")
    }
}
