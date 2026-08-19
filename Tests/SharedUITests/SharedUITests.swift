import XCTest
import SwiftUI
@testable import SharedUI
@testable import Directory

@MainActor
final class SharedUITests: XCTestCase {
    func testModuleCompiles() {
        _ = SharedUI.self
    }

    func testThemeColourReadsSixDigitHex() {
        XCTAssertEqual(ThemeColor.color("#0A84FF"), Color(red: 10 / 255, green: 132 / 255, blue: 255 / 255))
    }

    func testThemeColourFallsBackOnUnreadableValues() {
        XCTAssertEqual(ThemeColor.color("nope"), .black)
    }

    func testProfileCardBuildsForAMember() {
        let member = TeamMember(id: "aj", name: "Abbey Jackson", role: "Product Builder",
                                posts: 128, followers: 2400)
        _ = ProfileCardView(member: member)
    }
}
