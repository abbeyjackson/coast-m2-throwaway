/// Theme tokens — seeded from the supplied designs (D101).
/// The single theme file (D35): every formatting value lives here and
/// only the Theming agent modifies it. Values carry the design's own
/// token names.
public enum Theme {
    public enum Colors {
        public static let accent = "#0A84FF"
        public static let avatarGradient = "#0A84FF"
        public static let avatarGradientEnd = "#5E5CE6"
        public static let background = "#F2F2F7"
        public static let buttonTextOnAccent = "#FFFFFF"
        public static let cardSurface = "#FFFFFF"
        public static let neutral = "#E5E5EA"
        public static let primaryText = "#1C1C1E"
        public static let secondaryText = "#8E8E93"
    }
    public enum Spacing {
        public static let space14 = 14.0
        public static let space18 = 18.0
        public static let space2 = 2.0
        public static let space24 = 24.0
        public static let space3 = 3.0
        public static let space4 = 4.0
    }
    public enum Radii {
        public static let avatar = 30.0
        public static let button = 12.0
        public static let card = 20.0
    }
    public enum Typography {
        public enum AvatarInitials {
            public static let size = 24.0
            public static let weight = "600"
        }
        public enum Button {
            public static let size = 15.0
            public static let weight = "600"
        }
        public enum Name {
            public static let size = 18.0
            public static let weight = "600"
        }
        public enum Role {
            public static let size = 14.0
            public static let weight = "400"
        }
        public enum StatLabel {
            public static let size = 12.0
            public static let weight = "500"
        }
        public enum StatValue {
            public static let size = 17.0
            public static let weight = "700"
        }
    }
}
