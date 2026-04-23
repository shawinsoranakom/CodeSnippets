def request_to_curl(request: Request) -> str:
    """
    Converts a :class:`~scrapy.Request` object to a curl command.

    :param :class:`~scrapy.Request`: Request object to be converted
    :return: string containing the curl command
    """
    method = request.method

    data = f"--data-raw '{request.body.decode('utf-8')}'" if request.body else ""

    headers = " ".join(
        f"-H '{k.decode()}: {v[0].decode()}'" for k, v in request.headers.items()
    )

    url = request.url
    cookies = ""
    if request.cookies:
        if isinstance(request.cookies, dict):
            cookie = "; ".join(f"{k}={v}" for k, v in request.cookies.items())
            cookies = f"--cookie '{cookie}'"
        elif isinstance(request.cookies, list):
            cookie = "; ".join(
                f"{next(iter(c.keys()))}={next(iter(c.values()))}"
                for c in request.cookies
            )
            cookies = f"--cookie '{cookie}'"

    curl_cmd = f"curl -X {method} {url} {data} {headers} {cookies}".strip()
    return " ".join(curl_cmd.split())