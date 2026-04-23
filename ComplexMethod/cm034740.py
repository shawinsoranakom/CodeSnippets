def readHAR(url: str) -> tuple[str, str]:
    api_key = None
    user_agent = None
    for path in get_har_files():
        with open(path, 'rb') as file:
            try:
                harFile = json.loads(file.read())
            except json.JSONDecodeError:
                # Error: not a HAR file!
                continue
            for v in harFile['log']['entries']:
                if v['request']['url'].startswith(url):
                    v_headers = get_headers(v)
                    if "authorization" in v_headers:
                        api_key = v_headers["authorization"].split(maxsplit=1).pop()
                    if "user-agent" in v_headers:
                        user_agent = v_headers["user-agent"]
    if api_key is None:
        raise NoValidHarFileError("No access token found in .har files")

    return api_key, user_agent