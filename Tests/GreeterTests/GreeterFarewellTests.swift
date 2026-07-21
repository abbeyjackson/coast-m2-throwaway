import XCTest
@testable import Greeter

final class GreeterFarewellTests: XCTestCase {
    func testFarewellWithName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.farewell(name: "Abbey"), "Goodbye, Abbey!")
    }

    func testFarewellWithNoArguments() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.farewell(), "Goodbye!")
    }
}
