def pre_build_instructions(requirements: str) -> str:
    """Parse the given requirements and return any applicable pre-build instructions."""
    parsed_requirements = requirements.splitlines()

    package_versions = {
        match.group('package').lower(): match.group('version') for match
        in (re.search('^(?P<package>.*)==(?P<version>.*)$', requirement) for requirement in parsed_requirements)
        if match
    }

    instructions: list[str] = []

    build_constraints = (
        ('pyyaml', '>= 5.4, <= 6.0', ('Cython < 3.0',)),
    )

    for package, specifier, constraints in build_constraints:
        version_string = package_versions.get(package)

        if version_string:
            version = packaging.version.Version(version_string)
            specifier_set = packaging.specifiers.SpecifierSet(specifier)

            if specifier_set.contains(version):
                instructions.append(f'# pre-build requirement: {package} == {version}\n')

                for constraint in constraints:
                    instructions.append(f'# pre-build constraint: {constraint}\n')

    return ''.join(instructions)