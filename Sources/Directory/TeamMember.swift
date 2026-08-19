import Foundation

/// One person in the team directory.
public struct TeamMember: Identifiable, Equatable, Sendable {
    /// Stable identifier, used as the row and route key.
    public let id: String
    /// The member's name, spelled the way they want it shown.
    public var name: String
    /// What the member does on the team.
    public var role: String
    /// How many notes the member has published.
    public var posts: Int
    /// How many people follow the member.
    public var followers: Int
    /// Whether the person reading the directory follows this member.
    public var isFollowed: Bool

    /// Creates a directory member.
    ///
    /// - Parameters:
    ///   - id: Stable identifier for the member.
    ///   - name: The member's name as shown on screen.
    ///   - role: What the member does on the team.
    ///   - posts: How many notes the member has published.
    ///   - followers: How many people follow the member.
    ///   - isFollowed: Whether the reader already follows the member.
    public init(id: String, name: String, role: String, posts: Int,
                followers: Int, isFollowed: Bool = false) {
        self.id = id
        self.name = name
        self.role = role
        self.posts = posts
        self.followers = followers
        self.isFollowed = isFollowed
    }

    /// The one- or two-letter monogram the avatar shows.
    public var initials: String {
        let words = name.split(separator: " ").prefix(2)
        let letters = words.compactMap { $0.first }.map(String.init)
        return letters.isEmpty ? "?" : letters.joined().uppercased()
    }

    /// The follower count as the card prints it — thousands are shortened
    /// so a long number never pushes the stat row out of shape.
    public var followersLabel: String { Self.shortCount(followers) }

    /// The post count as the card prints it.
    public var postsLabel: String { Self.shortCount(posts) }

    /// Shortens a count the way the card shows it: 2400 reads as "2.4k".
    ///
    /// - Parameter count: The number to shorten.
    /// - Returns: The count as a display string.
    public static func shortCount(_ count: Int) -> String {
        guard count >= 1000 else { return String(count) }
        let thousands = Double(count) / 1000
        let rounded = (thousands * 10).rounded() / 10
        let whole = rounded == rounded.rounded()
        return whole ? "\(Int(rounded))k" : String(format: "%.1fk", rounded)
    }
}
