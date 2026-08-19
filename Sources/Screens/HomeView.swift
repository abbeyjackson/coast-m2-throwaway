import SwiftUI
import Greeter
import Directory
import SharedUI

/// The directory's home screen: the greeting, the section picker, and one
/// card per member.
public struct HomeView: View {
    private let directory: TeamDirectory
    private let reader: String

    /// Creates the home screen.
    ///
    /// - Parameters:
    ///   - directory: The store the screen reads from.
    ///   - reader: The name of the person reading the directory.
    public init(directory: TeamDirectory, reader: String = "Abbey") {
        self.directory = directory
        self.reader = reader
    }

    /// What the view draws.
    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Theme.Spacing.space18) {
                Text(directory.welcome(reader: reader))
                    .font(.system(size: Theme.Typography.Name.size, weight: .semibold))
                    .foregroundStyle(ThemeColor.primaryText)
                Text("Everyone on the team, and what they are working on.")
                    .font(.system(size: Theme.Typography.Role.size))
                    .foregroundStyle(ThemeColor.secondaryText)
                Button("Follow everyone") {
                    directory.followEveryone()
                }
                .font(.system(size: Theme.Typography.Button.size, weight: .semibold))
                .foregroundStyle(ThemeColor.accent)
                ForEach(directory.visibleMembers) { member in
                    ProfileCardView(member: member) {
                        directory.toggleFollow(id: member.id)
                    }
                }
            }
            .padding(Theme.Spacing.space24)
        }
        .background(ThemeColor.background)
    }
}
