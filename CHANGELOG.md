<!---
SPDX-FileCopyrightText: © 2022 Matt Williams <matt@milliams.com>
SPDX-License-Identifier: MIT
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2022-07-26

### Added

- Added an `--extra-args` argument to pass more arguments to the command
- The stdout, return code and run command are now returned as a `Result` object

### Removed

- The `--return` flag was removed as it's now always returned through the `Result` object.

### Fixed

- Added a small sleep to fix a rare race condition in interactive mode
- Added `pexpect` to the package dependencies

## [0.1.0] - 2022-07-22

### Added

- Initial release

[//]: # (C3-2-DKAC)
