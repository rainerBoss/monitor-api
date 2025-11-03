# Changelog


## [0.3.2] - 14.10.2025

### Changed
- Query now uses POST request. Discovered that URLs can exceed maximum length from too large query params

### Fixed
- Fixed concurrent requests all trying to login by adding another login check in login function


## [0.3.1] - 12.10.2025

### Changed
- Improved logging


## [0.3.0] - 29.08.2025

### Added
- Sumulate/Validate to batch command
- Type for batch command using TypedDict
- Optional boolean param for batch raise_on_error which will raise BatchCommandError if IsSuccessful field is False

### Changed
- Refactored retry logic. new method _make_api_request will handle both calling Query/Command API and doing retry


## [0.2.1] - 21.08.2025

### Fixed
- Forgot to remove async for SyncClient batch method
- Added '-> None' for both clients __init__ method because mypy was complaining when installing this library 


## [0.2.0] - 20.08.2025

### Added
- New separate SyncClient
- More detailed exceptions
- New waiting mechanism so any call that happens durring login process waits before making the call
- Support for /Validate, /Simulate and /Many

### Changed
- Renamed the single old client into AsyncClient
- Clients now use base_url parameter instead of host


## [0.1.0] - 07.30.2025

Release version
