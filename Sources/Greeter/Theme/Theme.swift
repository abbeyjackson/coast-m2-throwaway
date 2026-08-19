/// Theme tokens — seeded from the supplied designs (D101).
/// The single theme file (D35): every formatting value lives here and
/// only the Theming agent modifies it. Values carry the design's own
/// token names.
public enum Theme {
    /// The design's colours.
    public enum Colors {
        /// The design's accent value.
        public static let accent = "#0A84FF"
        /// The design's avatar gradient value.
        public static let avatarGradient = "#0A84FF"
        /// The design's avatar gradient end value.
        public static let avatarGradientEnd = "#5E5CE6"
        /// The design's background value.
        public static let background = "#F2F2F7"
        /// The design's button text on accent value.
        public static let buttonTextOnAccent = "#FFFFFF"
        /// The design's card surface value.
        public static let cardSurface = "#FFFFFF"
        /// The design's neutral value.
        public static let neutral = "#E5E5EA"
        /// The design's primary text value.
        public static let primaryText = "#1C1C1E"
        /// The design's secondary text value.
        public static let secondaryText = "#8E8E93"
    }
    /// The design's spacing values.
    public enum Spacing {
        /// The design's space14 value.
        public static let space14 = 14.0
        /// The design's space18 value.
        public static let space18 = 18.0
        /// The design's space2 value.
        public static let space2 = 2.0
        /// The design's space24 value.
        public static let space24 = 24.0
        /// The design's space3 value.
        public static let space3 = 3.0
        /// The design's space4 value.
        public static let space4 = 4.0
    }
    /// The design's corner radii.
    public enum Radii {
        /// The design's avatar value.
        public static let avatar = 30.0
        /// The design's button value.
        public static let button = 12.0
        /// The design's card value.
        public static let card = 20.0
    }
    /// The design's text styles.
    public enum Typography {
        /// The design's avatar initials text style.
        public enum AvatarInitials {
            /// How large this style's text is.
            public static let size = 24.0
            /// How heavy this style's text is.
            public static let weight = "600"
        }
        /// The design's button text style.
        public enum Button {
            /// How large this style's text is.
            public static let size = 15.0
            /// How heavy this style's text is.
            public static let weight = "600"
        }
        /// The design's name text style.
        public enum Name {
            /// How large this style's text is.
            public static let size = 18.0
            /// How heavy this style's text is.
            public static let weight = "600"
        }
        /// The design's role text style.
        public enum Role {
            /// How large this style's text is.
            public static let size = 14.0
            /// How heavy this style's text is.
            public static let weight = "400"
        }
        /// The design's stat label text style.
        public enum StatLabel {
            /// How large this style's text is.
            public static let size = 12.0
            /// How heavy this style's text is.
            public static let weight = "500"
        }
        /// The design's stat value text style.
        public enum StatValue {
            /// How large this style's text is.
            public static let size = 17.0
            /// How heavy this style's text is.
            public static let weight = "700"
        }
    }
}
