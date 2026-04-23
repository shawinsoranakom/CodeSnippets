def readHAR(url: str):
    api_key = None
    useridentitytype = None
    cookies = None
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
                    if "x-useridentitytype" in v_headers:
                        useridentitytype = v_headers["x-useridentitytype"]
                    if v['request']['cookies']:
                        cookies = {c['name']: c['value'] for c in v['request']['cookies']}
    if not cookies:
        raise NoValidHarFileError("No session found in .har files")

    return api_key, useridentitytype, cookies