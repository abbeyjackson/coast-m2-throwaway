// swift-tools-version: 6.0
// Throwaway target project driven by the Coast M1 walking skeleton.

import PackageDescription

let package = Package(
    name: "Greeter",
    targets: [
        .target(name: "Greeter"),
        .testTarget(name: "GreeterTests", dependencies: ["Greeter"]),
    ]
)
