def get_release_branch():
    """Retrieve the release branch from the release PR"""

    url = "https://api.github.com/repos/streamlit/streamlit/pulls"
    response = requests.get(url).json()

    # Response is in an array, must map over each pull (dict)
    for pull in response:
        ref = check_for_release_pr(pull)
        if ref != None:
            return ref