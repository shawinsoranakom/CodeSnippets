def check_pyproject_sections(pyproject_toml, min_dependencies):
    packages, pyproject_tags = extract_packages_and_pyproject_tags(min_dependencies)

    for pyproject_section, min_dependencies_tag in pyproject_tags.items():
        # Special situation for numpy: we have numpy>=2 in
        # build-system.requires to make sure we build wheels against numpy>=2.
        # TODO remove this when our minimum supported numpy version is >=2.
        skip_version_check_for = (
            ["numpy"] if pyproject_section == "build-system.requires" else []
        )

        expected_packages = packages[min_dependencies_tag]

        pyproject_section_keys = pyproject_section.split(".")
        info = pyproject_toml
        # iterate through nested keys to get packages and version
        for key in pyproject_section_keys:
            info = info[key]

        pyproject_build_min_versions = {}
        # Assuming pyproject.toml build section has something like "my-package>=2.3.0"
        pattern = r"([\w-]+)\s*[>=]=\s*([\d\w.]+)"
        for requirement in info:
            match = re.search(pattern, requirement)
            if match is None:
                raise NotImplementedError(
                    f"{requirement} does not match expected regex {pattern!r}. "
                    "Only >= and == are supported for version requirements"
                )

            package, version = match.group(1), match.group(2)

            pyproject_build_min_versions[package] = version

        msg = f"Packages in {pyproject_section} differ from _min_depencies.py"

        assert sorted(pyproject_build_min_versions) == sorted(expected_packages), msg

        for package, version in pyproject_build_min_versions.items():
            version = parse_version(version)
            expected_min_version = parse_version(min_dependencies[package][0])
            if package in skip_version_check_for:
                continue

            message = (
                f"{package} has inconsistent minimum versions in pyproject.toml and"
                f" _min_depencies.py: {version} != {expected_min_version}"
            )
            assert version == expected_min_version, message