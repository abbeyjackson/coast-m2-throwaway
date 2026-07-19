import XCTest
@testable import Greeter

final class GreeterTests: XCTestCase {
    func testGreetWithName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: "Ada"), "Hello, Ada!")
    }

    func testGreetWithNoArguments() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(), "Hello, world!")
    }

    func testGreetWithEmptyName() {
        let greeter = Greeter()
        XCTAssertEqual(greeter.greet(name: ""), "Hello, !")
    }
}
