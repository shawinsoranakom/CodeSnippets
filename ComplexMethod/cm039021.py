def get_min_version_with_wheel(package_name, python_version):
    # For compiled dependencies we want the oldest minor version that has
    # wheels for 'python_version'
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code != 200:
        return None

    data = response.json()
    releases = data["releases"]

    compatible_versions = []
    # We want only minor X.Y.0 and not bugfix X.Y.Z
    minor_releases = [
        (ver, release_info)
        for ver, release_info in releases.items()
        if re.match(r"^\d+\.\d+\.0$", ver)
    ]
    for ver, release_info in minor_releases:
        for file_info in release_info:
            if (
                file_info["packagetype"] == "bdist_wheel"
                and f"cp{python_version.replace('.', '')}" in file_info["filename"]
                and not file_info["yanked"]
            ):
                compatible_versions.append(ver)
                break

    if not compatible_versions:
        return None

    return min(compatible_versions, key=version.parse)