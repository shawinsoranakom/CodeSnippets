def verify_semver(version):
    """Verify if version is compliant with semantic versioning.

    https://semver.org/
    """

    try:
        return str(semver.VersionInfo.parse(version))
    except ValueError as e:
        raise (e)