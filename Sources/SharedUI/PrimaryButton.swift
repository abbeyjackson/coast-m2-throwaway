import SwiftUI
import Greeter

/// The one filled action button every screen uses.
public struct PrimaryButton: View {
    private let title: String
    private let isOn: Bool
    private let action: () -> Void

    /// Creates a primary button.
    ///
    /// - Parameters:
    ///   - title: The button's label.
    ///   - isOn: Whether the button shows its engaged (quiet) fill.
    ///   - action: What to run when the button is pressed.
    public init(title: String, isOn: Bool = false, action: @escaping () -> Void) {
        self.title = title
        self.isOn = isOn
        self.action = action
    }

    /// What the view draws.
    public var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: Theme.Typography.Button.size, weight: .semibold))
                .foregroundStyle(isOn ? ThemeColor.primaryText : ThemeColor.buttonTextOnAccent)
                .frame(maxWidth: .infinity)
                .padding(.vertical, Theme.Spacing.space14)
                .background(isOn ? ThemeColor.neutral : ThemeColor.accent)
                .clipShape(RoundedRectangle(cornerRadius: Theme.Radii.button))
        }
        .buttonStyle(.plain)
    }
}
