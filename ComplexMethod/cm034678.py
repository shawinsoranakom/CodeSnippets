def readHAR(request_config: RequestConfig):
    for path in get_har_files():
        with open(path, 'rb') as file:
            try:
                harFile = json.loads(file.read())
            except json.JSONDecodeError:
                # Error: not a HAR file!
                continue
            for v in harFile['log']['entries']:
                v_headers = get_headers(v)
                if arkose_url == v['request']['url']:
                    request_config.arkose_request = parseHAREntry(v)
                elif v['request']['url'].startswith(start_url):
                    try:
                        match = re.search(r'"accessToken":"(.*?)"', v["response"]["content"]["text"])
                        if match:
                            request_config.access_token = match.group(1)
                    except KeyError:
                        pass
                    try:
                        if "openai-sentinel-proof-token" in v_headers:
                            request_config.headers = v_headers
                            request_config.proof_token = json.loads(base64.b64decode(
                                v_headers["openai-sentinel-proof-token"].split("gAAAAAB", 1)[-1].encode()
                            ).decode())
                        if "openai-sentinel-turnstile-token" in v_headers:
                            request_config.turnstile_token = v_headers["openai-sentinel-turnstile-token"]
                        if "authorization" in v_headers:
                            request_config.access_token = v_headers["authorization"].split(" ")[1]
                        request_config.cookies = {c['name']: c['value'] for c in v['request']['cookies']}
                    except Exception as e:
                        debug.log(f"Error on read headers: {e}")