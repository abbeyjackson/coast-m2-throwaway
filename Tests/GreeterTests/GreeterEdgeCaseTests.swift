import XCTest
@testable import Greeter

/// Post-work unit tests (D24): edge cases and internal behavior for the
/// public `Greeter` type that sit below the plan's resolution. These
/// supplement, but do not replace, the requirement tests in
/// GreeterTests.swift.
final class GreeterEdgeCaseTests: XCTestCase {
    func testGreetWithEmptyNameReturnsGreetingWithEmptyName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: ""), "Hello, !")
    }

    func testGreetWithWhitespaceOnlyNameIsPreservedVerbatim() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "   "), "Hello,    !")
    }

    func testGreetWithLeadingAndTrailingWhitespaceIsPreservedVerbatim() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "  Ada  "), "Hello,   Ada  !")
    }

    func testGreetWithUnicodeNameIncludingEmoji() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "🚀Zoë"), "Hello, 🚀Zoë!")
    }

    func testGreetWithNameContainingSpecialCharacters() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "O'Brien & Sons, Inc."), "Hello, O'Brien & Sons, Inc.!")
    }

    func testGreetWithNameContainingNewlineIsPreservedVerbatim() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada\nLovelace"), "Hello, Ada\nLovelace!")
    }

    func testGreetWithVeryLongNameDoesNotTruncate() {
        let greeter = Greeter()
        let longName = String(repeating: "A", count: 10_000)
        XCTAssertEqual(greeter.greet(name: longName), "Hello, \(longName)!")
    }

    func testGreetWithNameEqualToWorldIsTreatedAsRegularName() {
        // Guards against the internal literal "world" from greet() being
        // conflated with a caller-supplied name equal to "world".
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "world"), "Hello, world!")
    }

    func testGreetNoArgumentsIsIdempotentAcrossMultipleCalls() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(), greeter.greet())
    }

    func testMultipleGreeterInstancesBehaveIdentically() {
        let first = Greeter()
        let second = Greeter()
        XCTAssertEqual(first.greet(name: "Grace"), second.greet(name: "Grace"))
        XCTAssertEqual(first.greet(), second.greet())
    }
}
