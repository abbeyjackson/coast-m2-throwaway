import XCTest
@testable import Directory

final class TeamMemberTests: XCTestCase {
    func testInitialsUseTheFirstTwoWords() {
        let member = TeamMember(id: "aj", name: "Abbey Jackson", role: "Product Builder",
                                posts: 1, followers: 2)
        XCTAssertEqual(member.initials, "AJ")
    }

    func testInitialsFallBackWhenTheNameIsEmpty() {
        let member = TeamMember(id: "x", name: "", role: "", posts: 0, followers: 0)
        XCTAssertEqual(member.initials, "?")
    }

    func testShortCountLeavesSmallNumbersAlone() {
        XCTAssertEqual(TeamMember.shortCount(999), "999")
    }

    func testShortCountShortensThousands() {
        XCTAssertEqual(TeamMember.shortCount(2400), "2.4k")
        XCTAssertEqual(TeamMember.shortCount(2000), "2k")
    }
}
