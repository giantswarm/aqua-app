# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project's packages adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [5.3.5] - 2021-04-30

### Changed

- Updated container image versions to `5.3.21119`.

## [5.3.4] - 2021-04-28

### Changed

- Updated container image versions to `5.3.21112`.

## [5.3.3] - 2021-03-19

### Added

- Scanner: re-added option to provide credentials through secret

## [5.3.2] - 2021-03-10

### Fixed

- Schema validation
- Incorrect datatype for .Values.web.ingress.hosts and .Values.envoy.service.annotations
- Ambiguity for port configurations. now accepts strings or integers

## [5.3.1] - 2021-03-08

### Update

This chart now tracks the Giant Swarm platform specific branch of upstream.

### Fixes

- How existing secrets for DB credentials work
- DB permission template
- Linting issue and the values.schema.yaml

### Added

- Security context to all relevant resources
- Advanced configuration section from upstream to README.md

## [5.3.0] - 2021-01-12

### Changed

- Updated all charts to upstream 5.3. ([#34](https://github.com/giantswarm/aqua-app/pull/34))

### Added

- Added values.schema.json to validate default values

## [4.6.3] - 2020-09-02

### Changed

- Upgrade to 4.6.20236 
- **Enforcer**: Remove **AQUA_NETWORK_CONTROL** environment variable
- **Enforcer**: Add **AQUA_GRPC_KEEP_ALIVE_INTERVAL** environment variable default configuration
- **Enforcer**: Configure default memory limit 10 **1500MiB**
- **Gateway**: Add **AQUA_WORLOADS_PING_CHECK** environment variable default configuration
- **Gateway**: Add **AQUA_DISCONNECTION_GRACE_PERIOD** environment variable default configuration
- **Gateway**: Adjusted default memory request/limit to **10GB** & and remove cpu request/limit
- **Console**: Adjusted default memory request/limit to **10GB** & and remove cpu request/limit
- **Database**: Adjusted default memory request/limit to **15GB** & and remove cpu request/limit

## [4.6.2] 2020-07-02

### Changed

- Gateway/Console: ensure boolean env vars are quoted.

## [4.6.1] 2020-07-01

### Changed

- Gateway: allow configuration of asset integrity checking (default to `true`).
- Console: allow configuration of workload integrity checking (default to `true`).
- Enforcer: allow configuration of memory pressure behaviour (default to `critical`).
- Enforcer: allow configuration of network failure behaviour (default to `open`).

## [4.6.0] 2020-06-09

### Changed

- Updated image versions from `4.5.20069` to `4.6.20156`.

[Unreleased]: https://github.com/giantswarm/aqua-app/compare/v5.3.5...HEAD
[5.3.5]: https://github.com/giantswarm/aqua-app/compare/v5.3.4...v5.3.5
[5.3.4]: https://github.com/giantswarm/aqua-app/compare/v5.3.3...v5.3.4
[5.3.3]: https://github.com/giantswarm/aqua-app/compare/v5.3.2...v5.3.3
[5.3.2]: https://github.com/giantswarm/aqua-app/compare/v5.3.1...v5.3.2
[5.3.1]: https://github.com/giantswarm/aqua-app/compare/v5.3.0...v5.3.1
[5.3.0]: https://github.com/giantswarm/aqua-app/compare/v4.6.3...v5.3.0
[4.6.3]: https://github.com/giantswarm/aqua-app/compare/v4.6.2...v4.6.3
[4.6.2]: https://github.com/giantswarm/aqua-app/compare/v4.6.1...v4.6.2
[4.6.1]: https://github.com/giantswarm/aqua-app/compare/v4.6.0...v4.6.1
[4.6.0]: https://github.com/giantswarm/aqua-app/releases/tag/v4.6.0
