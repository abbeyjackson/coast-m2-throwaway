import SwiftUI
import Greeter
import Directory
import SharedUI

/// The settings screen: which grouping home opens on, and signing out.
public struct SettingsView: View {
    private let directory: TeamDirectory
    private let reader: String
    @State private var section: DirectorySection
    @State private var signOff = ""

    /// Creates the settings screen.
    ///
    /// - Parameters:
    ///   - directory: The store the picked section is written to.
    ///   - reader: The name of the person reading the directory.
    public init(directory: TeamDirectory, reader: String = "Abbey") {
        self.directory = directory
        self.reader = reader
        _section = State(initialValue: directory.section)
    }

    /// What the view draws.
    public var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.space18) {
            Text("Settings")
                .font(.system(size: Theme.Typography.Name.size, weight: .semibold))
                .foregroundStyle(ThemeColor.primaryText)
            Text("Home opens on")
                .font(.system(size: Theme.Typography.StatLabel.size, weight: .medium))
                .foregroundStyle(ThemeColor.secondaryText)
            ForEach(DirectorySection.allCases, id: \.self) { option in
                PrimaryButton(title: option.title, isOn: option != section) {
                    section = option
                    directory.section = option
                }
            }
            Button("Sign out") {
                signOff = directory.signOffLine(reader: reader)
            }
            .font(.system(size: Theme.Typography.Button.size, weight: .semibold))
            .foregroundStyle(ThemeColor.accent)
            Text(signOff)
                .font(.system(size: Theme.Typography.Role.size))
                .foregroundStyle(ThemeColor.secondaryText)
        }
        .padding(Theme.Spacing.space24)
        .background(ThemeColor.background)
    }
}
