import XCTest
@testable import Greeter

/// Tests for behavior below the requirement tests' resolution: boundaries
/// that aren't a distinct input variation of the same "format a greeting"
/// path, but pin properties of the type itself.
final class GreeterBoundaryTests: XCTestCase {
    /// A single `Greeter` instance holds no state between calls: reusing it
    /// for different names must not cache, mutate, or bleed results across
    /// calls.
    func testGreetIsStatelessAcrossRepeatedCallsOnSameInstance() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada"), "Hello, Ada!")
        XCTAssertEqual(greeter.greet(name: "Grace"), "Hello, Grace!")
        XCTAssertEqual(greeter.greet(name: "Ada"), "Hello, Ada!")
    }

    /// The greeting performs no trimming/sanitization of its input: a name
    /// that is only whitespace is preserved verbatim rather than being
    /// treated as if it were empty.
    func testGreetDoesNotTrimWhitespaceOnlyName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "   "), "Hello,    !")
    }
}
