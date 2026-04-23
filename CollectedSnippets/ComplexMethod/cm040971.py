def fetch_latest_versions() -> dict[str, str]:  # pragma: no cover
    """
    Fetches from the opensearch git repository tags the latest patch versions for a minor version and returns a
    dictionary where the key corresponds to the minor version, and the value to the patch version. Run this once in a
    while and update the ``install_versions`` constant in this file.

    Example::

        {
            '1.0': '1.0.0',
            '1.1': '1.1.0',
            '1.2': '1.2.2'
        }

    When updating the versions, make sure to not add versions which are currently not yet supported by AWS.

    :returns: a version dictionary
    """
    from collections import defaultdict

    import requests

    versions = []

    i = 0
    while True:
        tags_raw = requests.get(
            f"https://api.github.com/repos/opensearch-project/OpenSearch/tags?per_page=100&page={i}"
        )
        tags = tags_raw.json()
        i += 1
        if not tags:
            break
        versions.extend([tag["name"].lstrip("v") for tag in tags])

    sem_versions = []

    for v in versions:
        try:
            sem_version = semver.VersionInfo.parse(v)
            if not sem_version.prerelease:
                sem_versions.append(sem_version)
        except ValueError:
            pass

    minor = defaultdict(list)

    for ver in sem_versions:
        minor[f"{ver.major}.{ver.minor}"].append(ver)

    return {k: str(max(versions)) for k, versions in minor.items()}