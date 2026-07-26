import XCTest
@testable import SharedUI

/// Scaffold test so the SharedUI target is built by the suite. The engine adds
/// the real view tests (construction-only — no display needed on CI).
final class SharedUIScaffoldTests: XCTestCase {
    func testModuleCompiles() {
        _ = SharedUI.self
    }
}
