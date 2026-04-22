def check_last_rc():
    """Checks PyPI for existing release candidates"""

    current_version = os.getenv("DESIRED_VERSION")

    url = "https://pypi.org/pypi/streamlit/json"
    response = requests.get(url).json()
    all_releases = response["releases"].keys()

    current_version_candidates = sorted(
        [x for x in all_releases if "rc" in x and current_version in x]
    )

    if current_version_candidates:
        latest_release_candidate = current_version_candidates[-1]
        return latest_release_candidate
    else:
        return None