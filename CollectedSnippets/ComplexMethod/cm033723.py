def supported_python_versions(self) -> t.Optional[tuple[str, ...]]:
        """A tuple of supported Python versions or None if the test does not depend on specific Python versions."""
        versions = super().supported_python_versions

        if self.controller_only:
            versions = tuple(version for version in versions if version in CONTROLLER_PYTHON_VERSIONS)

        if self.minimum_python_version:
            versions = tuple(version for version in versions if str_to_version(version) >= str_to_version(self.minimum_python_version))

        if self.maximum_python_version:
            versions = tuple(version for version in versions if str_to_version(version) <= str_to_version(self.maximum_python_version))

        if self.min_max_python_only:
            versions = versions[0], versions[-1]

        return versions