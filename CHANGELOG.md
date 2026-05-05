# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project adheres to both [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## [UNRELEASED]

## [0.0.5] - 2026-05-05

### Added

- Expose `iscoroutinefunction` and `markcoroutinefunction` functions.
- `iterate_queue` async generator to consume an `asyncio.Queue` as an `async for` loop, stopping automatically when the queue is shut down.
- Expose `iscoroutinefunction` and `markcoroutinefunction` functions.
- `iterate_queue` async generator to consume an `asyncio.Queue` as an `async for` loop, stopping automatically when the queue is shut down or when the `STOP` sentinel is dequeued.
- `fill_queue` coroutine to fill an `asyncio.Queue` from any sync or async iterable.
- `merge_iterables` async context manager to merge multiple sync or async iterables into a single interleaved stream.
- `STOP` sentinel object used to signal the end of an `iterate_queue` stream.

### Changed

- Rename `noop` to `identity` so the utility clearly expresses returning the passed value after yielding once to the event loop.


### Changed

- Renamed `noop` to `identity` so the utility clearly expresses returning the passed value after yielding once to the event loop.

## [0.0.4] - 2026-03-18

### Added

- `asyncify` function to wrap synchronous callables so they can be awaited, running them in a separate thread via `asyncio.to_thread`.

## [0.0.3] - 2026-02-26

### Added

- This CHANGELOG file.
- pre-commit config.
- test coverage using Codecov
- LimitedTaskGroup to execute tasks limiting concurrency
- heartbeat function to run something at regular interval

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

[unreleased]: https://github.com/hartungstenio/asyncio-extensions/compare/0.0.5...HEAD
[0.0.5]: https://github.com/hartungstenio/asyncio-extensions/compare/0.0.4...0.0.5
[0.0.4]: https://github.com/hartungstenio/asyncio-extensions/compare/0.0.3...0.0.4
[0.0.3]: https://github.com/hartungstenio/asyncio-extensions/compare/0.0.2...0.0.3
[0.0.2]: https://github.com/hartungstenio/asyncio-extensions/compare/0.0.1...0.0.2
[0.0.1]: https://github.com/hartungstenio/asyncio-extensions/releases/tag/0.0.1
