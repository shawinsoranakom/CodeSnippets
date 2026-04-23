def create_release():
    """Create a release from the Git Tag"""

    tag = os.getenv("GIT_TAG")
    access_token = os.getenv("GH_TOKEN")

    if not tag:
        raise Exception("Unable to retrieve GIT_TAG environment variable")

    url = "https://api.github.com/repos/streamlit/streamlit/releases"
    header = {"Authorization": f"token {access_token}"}
    payload = {"tag_name": tag, "name": tag}

    response = requests.post(url, json=payload, headers=header)

    if response.status_code == 201:
        print(f"Successfully created Release {tag}")
    else:
        raise Exception(f"Unable to create release, HTTP response: {response.text}")