def get_min_version_pure_python_or_example_dependency(
    package_name, scikit_learn_release_date_str="today"
):
    # for pure Python dependencies we want the most recent minor release that
    # is at least 2 years old
    if scikit_learn_release_date_str == "today":
        scikit_learn_release_date = pd.to_datetime(datetime.now().date())
    else:
        scikit_learn_release_date = datetime.strptime(
            scikit_learn_release_date_str, "%Y-%m-%d"
        )

    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code != 200:
        return None

    data = response.json()
    releases = data["releases"]

    compatible_versions = []
    # We want only minor X.Y.0 and not bugfix X.Y.Z
    releases = [
        (ver, release_info)
        for ver, release_info in releases.items()
        if re.match(r"^\d+\.\d+\.0$", ver)
    ]
    for ver, release_info in releases:
        for file_info in release_info:
            if (
                file_info["packagetype"] == "bdist_wheel"
                and not file_info["yanked"]
                and (
                    scikit_learn_release_date - pd.to_datetime(file_info["upload_time"])
                ).days
                > 365 * 2
            ):
                compatible_versions.append(ver)
                break

    if not compatible_versions:
        return None

    return max(compatible_versions, key=version.parse)