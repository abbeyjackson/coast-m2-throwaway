import Foundation

/// The three groupings the home screen offers.
public enum DirectorySection: String, CaseIterable, Sendable {
    /// Everyone in the directory.
    case everyone
    /// Only the members the reader follows.
    case following
    /// Members who joined in the last thirty days.
    case newcomers

    /// The section's name, as the picker prints it.
    public var title: String {
        switch self {
        case .everyone: return "Everyone"
        case .following: return "Following"
        case .newcomers: return "New this month"
        }
    }
}
