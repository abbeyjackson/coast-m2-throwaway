import SwiftUI
import Greeter
import Directory
import SharedUI

/// One member's own screen: their card, and the note that opens it.
public struct MemberProfileView: View {
    private let member: TeamMember
    private let directory: TeamDirectory

    /// Creates the member profile screen.
    ///
    /// - Parameters:
    ///   - member: The person the screen is about.
    ///   - directory: The store the follow button writes to.
    public init(member: TeamMember, directory: TeamDirectory) {
        self.member = member
        self.directory = directory
    }

    /// What the view draws.
    public var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.space24) {
            ProfileCardView(member: member) {
                directory.toggleFollow(id: member.id)
            }
            VStack(alignment: .leading, spacing: Theme.Spacing.space4) {
                Text("About")
                    .font(.system(size: Theme.Typography.StatLabel.size, weight: .medium))
                    .foregroundStyle(ThemeColor.secondaryText)
                Text("\(member.name) has published \(member.postsLabel) notes.")
                    .font(.system(size: Theme.Typography.Role.size))
                    .foregroundStyle(ThemeColor.primaryText)
            }
        }
        .padding(Theme.Spacing.space24)
        .background(ThemeColor.background)
    }
}
