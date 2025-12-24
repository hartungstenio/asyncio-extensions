# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project adheres to both [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## [UNRELEASED]

### Added

- This CHANGELOG file.
- pre-commit config.

### Changed

- Package building and publishing are run in separate jobs to avoid credential sharing.
- Improved README

## [0.0.2] - 2025-12-23

### Changed

- `TaskGroup` now inherits from `asyncio.TaskGroup`.

## [0.0.1] - 2025-12-23

### Added

- `TaskGroup` subclass with a cancel method.
- `checkpoint` function to yield control to the event loop.
- `sleep_forever` function.

[unreleased]: https://github.com/hartungstenio/asyncio-extensions/compare/0.0.2...HEAD
[0.0.2]: https://github.com/hartungstenio/asyncio-extensions/compare/0.0.1...0.0.2
[0.0.1]: https://github.com/hartungstenio/asyncio-extensions/releases/tag/0.0.1
