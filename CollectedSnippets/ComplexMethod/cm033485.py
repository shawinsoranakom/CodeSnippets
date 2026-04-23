def apply(self, version: Version) -> Version:
        """Apply the mode to the given version and return the result."""
        original_version = version

        release_component_count = 3

        if len(version.release) != release_component_count:
            raise ApplicationError(f"Version {version} contains {version.release} release components instead of {release_component_count}.")

        if version.epoch:
            raise ApplicationError(f"Version {version} contains an epoch component: {version.epoch}")

        if version.local is not None:
            raise ApplicationError(f"Version {version} contains a local component: {version.local}")

        if version.is_devrelease and version.is_postrelease:
            raise ApplicationError(f"Version {version} is a development and post release version.")

        if self == VersionMode.ALLOW_DEV_POST:
            return version

        if self == VersionMode.REQUIRE_DEV_POST:
            if not version.is_devrelease and not version.is_postrelease:
                raise ApplicationError(f"Version {version} is not a development or post release version.")

            return version

        if version.is_devrelease:
            raise ApplicationError(f"Version {version} is a development release: {version.dev}")

        if self == VersionMode.STRIP_POST:
            if version.is_postrelease:
                version = Version(str(version).removesuffix(f".post{version.post}"))
                display.warning(f"Using version {version} by stripping the post release suffix from version {original_version}.")

            return version

        if self == VersionMode.REQUIRE_POST:
            if not version.is_postrelease:
                raise ApplicationError(f"Version {version} is not a post release version.")

            return version

        if version.is_postrelease:
            raise ApplicationError(f"Version {version} is a post release.")

        if self == VersionMode.DEFAULT:
            return version

        raise NotImplementedError(self)