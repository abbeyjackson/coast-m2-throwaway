import XCTest
@testable import Screens
@testable import Directory

@MainActor
final class ScreensTests: XCTestCase {
    func testHomeBuilds() {
        _ = HomeView(directory: TeamDirectory())
    }

    func testMemberProfileBuilds() {
        let directory = TeamDirectory()
        _ = MemberProfileView(member: TeamDirectory.sample[0], directory: directory)
    }

    func testSettingsOpensOnTheDirectorysSection() {
        let directory = TeamDirectory(section: .newcomers)
        _ = SettingsView(directory: directory)
        XCTAssertEqual(directory.section, .newcomers)
    }
}
