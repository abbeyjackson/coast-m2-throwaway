import XCTest
@testable import Greeter

final class GreeterEdgeCaseTests: XCTestCase {
    func testGreetWithEmptyNameProducesGreetingWithEmptyPlaceholder() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: ""), "Hello, !")
    }

    func testGreetDoesNotTrimWhitespaceInName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "  Ada  "), "Hello,   Ada  !")
    }
}
