import XCTest
@testable import Greeter

/// Scaffold seed: proves the suite runs green on an empty module.
final class ScaffoldTests: XCTestCase {
    func testScaffoldIsAlive() {
        XCTAssertNotNil(GreeterModule.self)
    }
}
