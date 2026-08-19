import XCTest
@testable import Directory

final class TeamDirectoryTests: XCTestCase {
    func testFollowingSectionShowsOnlyFollowedMembers() {
        let directory = TeamDirectory(section: .following)
        XCTAssertEqual(directory.visibleMembers.map(\.id), ["aj"])
    }

    func testTogglingFollowMovesTheFollowerCount() {
        let directory = TeamDirectory()
        let before = directory.member(id: "rm")?.followers
        XCTAssertEqual(directory.toggleFollow(id: "rm"), true)
        XCTAssertEqual(directory.member(id: "rm")?.followers, (before ?? 0) + 1)
    }

    func testTogglingAnUnknownMemberChangesNothing() {
        let directory = TeamDirectory()
        XCTAssertNil(directory.toggleFollow(id: "nobody"))
    }

    func testWelcomeUsesTheGreeterModule() {
        XCTAssertEqual(TeamDirectory().welcome(reader: "Abbey"), "Hello, Abbey!")
    }

    func testSignOffUsesTheGreeterModule() {
        XCTAssertEqual(TeamDirectory().signOffLine(reader: "Abbey"), "Goodbye, Abbey!")
    }
}
