def get_api_token():
    # Read token from ENV, otherwise read from the ~/.transifexrc file.
    api_token = os.getenv("TRANSIFEX_API_TOKEN")
    if not api_token:
        parser = ConfigParser()
        parser.read(os.path.expanduser("~/.transifexrc"))
        api_token = parser.get("https://www.transifex.com", "token")

    assert api_token, "Please define the TRANSIFEX_API_TOKEN env var."
    return api_token