def test_all_versions_have_a_file_name_defined(self, file_names_mapping: list[VersionComponentMapping]) -> None:
        """Ensure all supported versions have a file name defined."""
        if not file_names_mapping:
            msg = f"file_names_mapping is empty for {self.__class__.__name__}. Skipping versions test."
            pytest.skip(msg)

        version_mappings = {mapping["version"]: mapping for mapping in file_names_mapping}

        for version in SUPPORTED_VERSIONS:
            if version not in version_mappings:
                supported_versions = ", ".join(sorted(m["version"] for m in file_names_mapping))
                msg = (
                    f"Version {version} not found in file_names_mapping for {self.__class__.__name__}.\n"
                    f"Currently defined versions: {supported_versions}\n"
                    "Please add this version to your component's file_names_mapping."
                )
                raise AssertionError(msg)

            mapping = version_mappings[version]
            if mapping["file_name"] is None:
                msg = (
                    f"file_name is None for version {version} in {self.__class__.__name__}.\n"
                    "Please provide a valid file_name in file_names_mapping or set it to DID_NOT_EXIST."
                )
                raise AssertionError(msg)

            if mapping["module"] is None:
                msg = (
                    f"module is None for version {version} in {self.__class__.__name__}.\n"
                    "Please provide a valid module name in file_names_mapping or set it to DID_NOT_EXIST."
                )
                raise AssertionError(msg)