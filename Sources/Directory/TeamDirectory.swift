import Foundation
import Greeter

/// The store every directory screen reads from: the members, the section
/// the reader is looking at, and the follow state they have changed.
public final class TeamDirectory {
    /// Everyone in the directory, in the order the list shows them.
    public private(set) var members: [TeamMember]
    /// The grouping the home screen is showing.
    public var section: DirectorySection
    private let greeter = Greeter()

    /// Creates a directory over the given members.
    ///
    /// - Parameters:
    ///   - members: The people the directory holds.
    ///   - section: The grouping to open on.
    public init(members: [TeamMember] = TeamDirectory.sample,
                section: DirectorySection = .everyone) {
        self.members = members
        self.section = section
    }

    /// The members the current section shows.
    public var visibleMembers: [TeamMember] {
        switch section {
        case .everyone: return members
        case .following: return members.filter(\.isFollowed)
        case .newcomers: return members.suffix(2).map { $0 }
        }
    }

    /// The line the home screen greets the reader with.
    ///
    /// - Parameter reader: The name of the person reading the directory.
    /// - Returns: The greeting, formatted by the Greeter module.
    public func welcome(reader: String) -> String {
        greeter.greet(name: reader)
    }

    /// The line the home screen shows when the reader signs out.
    ///
    /// - Parameter reader: The name of the person leaving.
    /// - Returns: The farewell, formatted by the Greeter module.
    public func signOffLine(reader: String) -> String {
        greeter.farewell(name: reader)
    }

    /// Looks a member up by identifier.
    ///
    /// - Parameter id: The member's identifier.
    /// - Returns: The member, or nil when the directory has no such person.
    public func member(id: String) -> TeamMember? {
        members.first { $0.id == id }
    }

    /// Follows or unfollows a member, and moves the follower count with it.
    ///
    /// - Parameter id: The member to toggle.
    /// - Returns: The member's new follow state, or nil when there is no
    ///   such member.
    @discardableResult
    public func toggleFollow(id: String) -> Bool? {
        guard let index = members.firstIndex(where: { $0.id == id }) else { return nil }
        members[index].isFollowed.toggle()
        members[index].followers += members[index].isFollowed ? 1 : -1
        return members[index].isFollowed
    }

    /// Follows everyone the current section shows, in one go.
    ///
    /// - Returns: How many people the reader started following.
    @discardableResult
    public func followEveryone() -> Int {
        var followed = 0
        for member in visibleMembers where !member.isFollowed {
            toggleFollow(id: member.id)
            followed += 1
        }
        return followed
    }

    /// The people the directory opens with.
    public static let sample: [TeamMember] = [
        TeamMember(id: "aj", name: "Abbey Jackson", role: "Product Builder",
                   posts: 128, followers: 2400, isFollowed: true),
        TeamMember(id: "rm", name: "Rosa Mendes", role: "Design Lead",
                   posts: 64, followers: 1820),
        TeamMember(id: "kt", name: "Kenji Tanaka", role: "Platform Engineer",
                   posts: 41, followers: 960),
        TeamMember(id: "no", name: "Nia Okafor", role: "Support",
                   posts: 12, followers: 240),
    ]
}
