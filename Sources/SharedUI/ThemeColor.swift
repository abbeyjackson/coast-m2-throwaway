import SwiftUI
import Greeter

/// Turns the theme's hex strings into SwiftUI colours, so every view reads
/// its colours from the one theme file and never writes a literal.
public enum ThemeColor {
    /// The card background behind every screen.
    public static var background: Color { color(Theme.Colors.background) }
    /// The surface a card is drawn on.
    public static var cardSurface: Color { color(Theme.Colors.cardSurface) }
    /// Text that carries the meaning of a row.
    public static var primaryText: Color { color(Theme.Colors.primaryText) }
    /// Supporting text beside the primary line.
    public static var secondaryText: Color { color(Theme.Colors.secondaryText) }
    /// The accent every action uses.
    public static var accent: Color { color(Theme.Colors.accent) }
    /// The label colour on top of the accent.
    public static var buttonTextOnAccent: Color { color(Theme.Colors.buttonTextOnAccent) }
    /// The quiet fill behind an inactive control.
    public static var neutral: Color { color(Theme.Colors.neutral) }
    /// The gradient the avatar is filled with.
    public static var avatarGradient: LinearGradient {
        LinearGradient(colors: [color(Theme.Colors.avatarGradient),
                                color(Theme.Colors.avatarGradientEnd)],
                       startPoint: .topLeading, endPoint: .bottomTrailing)
    }

    /// Reads one "#RRGGBB" theme value as a colour.
    ///
    /// - Parameter hex: The theme value, with or without a leading "#".
    /// - Returns: The colour the value names; black when it cannot be read.
    public static func color(_ hex: String) -> Color {
        var value = hex
        if value.hasPrefix("#") { value.removeFirst() }
        guard value.count == 6, let number = UInt32(value, radix: 16) else { return .black }
        return Color(red: Double((number >> 16) & 0xFF) / 255,
                     green: Double((number >> 8) & 0xFF) / 255,
                     blue: Double(number & 0xFF) / 255)
    }
}
