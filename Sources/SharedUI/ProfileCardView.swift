import SwiftUI
import Greeter
import Directory

/// The profile card from the design: avatar, name and role, the stat row,
/// and the follow button.
public struct ProfileCardView: View {
    private let member: TeamMember
    private let onToggleFollow: () -> Void

    /// Creates a profile card for one member.
    ///
    /// - Parameters:
    ///   - member: The person the card shows.
    ///   - onToggleFollow: What to run when the follow button is pressed.
    public init(member: TeamMember, onToggleFollow: @escaping () -> Void = {}) {
        self.member = member
        self.onToggleFollow = onToggleFollow
    }

    /// What the view draws.
    public var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.space18) {
            HStack(spacing: Theme.Spacing.space14) {
                Text(member.initials)
                    .font(.system(size: Theme.Typography.AvatarInitials.size, weight: .semibold))
                    .foregroundStyle(ThemeColor.buttonTextOnAccent)
                    .frame(width: Theme.Radii.avatar * 2, height: Theme.Radii.avatar * 2)
                    .background(ThemeColor.avatarGradient)
                    .clipShape(Circle())
                VStack(alignment: .leading, spacing: Theme.Spacing.space3) {
                    Text(member.name)
                        .font(.system(size: Theme.Typography.Name.size, weight: .semibold))
                        .foregroundStyle(ThemeColor.primaryText)
                    Text(member.role)
                        .font(.system(size: Theme.Typography.Role.size))
                        .foregroundStyle(ThemeColor.secondaryText)
                }
            }
            HStack(spacing: Theme.Spacing.space24) {
                StatBadgeView(value: member.postsLabel, label: "Posts")
                StatBadgeView(value: member.followersLabel, label: "Followers")
            }
            .padding(.horizontal, Theme.Spacing.space2)
            .padding(.vertical, Theme.Spacing.space4)
            PrimaryButton(title: member.isFollowed ? "Following" : "Follow",
                          isOn: member.isFollowed,
                          action: onToggleFollow)
        }
        .padding(Theme.Spacing.space24)
        .background(ThemeColor.cardSurface)
        .clipShape(RoundedRectangle(cornerRadius: Theme.Radii.card))
    }
}
