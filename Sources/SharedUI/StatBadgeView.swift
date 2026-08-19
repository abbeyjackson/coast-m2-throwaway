import SwiftUI
import Greeter

/// One number and its label, as the profile card's stat row prints them.
public struct StatBadgeView: View {
    private let value: String
    private let label: String

    /// Creates a stat badge.
    ///
    /// - Parameters:
    ///   - value: The number, already shortened for display.
    ///   - label: What the number counts.
    public init(value: String, label: String) {
        self.value = value
        self.label = label
    }

    /// What the view draws.
    public var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.space2) {
            Text(value)
                .font(.system(size: Theme.Typography.StatValue.size, weight: .bold))
                .foregroundStyle(ThemeColor.primaryText)
            Text(label)
                .font(.system(size: Theme.Typography.StatLabel.size, weight: .medium))
                .foregroundStyle(ThemeColor.secondaryText)
        }
    }
}
