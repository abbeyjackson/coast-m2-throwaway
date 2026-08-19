// swift-tools-version: 6.0
// Throwaway target project driven by the Coast M1 walking skeleton.

import PackageDescription

let package = Package(
    name: "Greeter",
    // macOS so the UI layer can build Apple frameworks (SwiftUI).
    platforms: [.macOS(.v13)],
    targets: [
        .target(name: "Greeter"),
        .testTarget(name: "GreeterTests", dependencies: ["Greeter"]),
        // The team directory's data: the members, and the store the screens
        // read from.
        .target(name: "Directory", dependencies: ["Greeter"]),
        .testTarget(name: "DirectoryTests", dependencies: ["Directory"]),
        // Shared UI components — the uiLib path class (Sources/SharedUI/**);
        // the engine builds views here against the seeded Theme.
        .target(name: "SharedUI", dependencies: ["Greeter", "Directory"]),
        .testTarget(name: "SharedUITests", dependencies: ["SharedUI"]),
        // The screens themselves, assembled from the shared components.
        .target(name: "Screens", dependencies: ["Greeter", "Directory", "SharedUI"]),
        .testTarget(name: "ScreensTests", dependencies: ["Screens"]),
    ]
)
