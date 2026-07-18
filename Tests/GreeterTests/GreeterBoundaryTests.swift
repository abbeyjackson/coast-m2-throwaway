import XCTest
@testable import Greeter

/// Boundary tests for behavior below the requirement tests' resolution:
/// confirms `greet(name:)` does plain interpolation without trimming or
/// special-character interpretation, which the requirement tests do not pin.
final class GreeterBoundaryTests: XCTestCase {
    func testGreetDoesNotTrimWhitespaceInName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "  Ada  "), "Hello,   Ada  !")
    }

    func testGreetDoesNotInterpretFormatSpecifiersInName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "100% \\ %@"), "Hello, 100% \\ %@!")
    }
}
