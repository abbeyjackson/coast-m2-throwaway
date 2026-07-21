import XCTest
@testable import Greeter

/// Locks boundary behavior of Greeter.farewell(name:) not already pinned by
/// GreeterFarewellTests: that the name is passed through untouched (no
/// trimming/sanitizing) and that non-ASCII input is handled correctly.
final class GreeterFarewellBoundaryTests: XCTestCase {
    func testFarewellPreservesWhitespaceInName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.farewell(name: "  Ada  "), "Goodbye,   Ada  !")
    }

    func testFarewellWithUnicodeName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.farewell(name: "日本語"), "Goodbye, 日本語!")
    }
}
