def parse_context(curl_command):
    method = "get"
    if not curl_command or not curl_command.strip():
        return ParsedContext(
            method=method, url="", data=None, headers={}, cookies={}, verify=True, auth=None, proxy=None
        )

    # Strip whitespace to handle formatting issues
    curl_command = curl_command.strip()
    parsed_args: ParsedArgs = parse_curl_command(curl_command)

    # Safeguard against missing parsed_args attributes
    post_data = getattr(parsed_args, "data", None) or getattr(parsed_args, "data_binary", None)
    if post_data:
        method = "post"

    # Prioritize explicit method from -X flag
    if getattr(parsed_args, "method", None):
        method = parsed_args.method.lower()

    cookie_dict = OrderedDict()
    quoted_headers = OrderedDict()

    # Process headers safely
    for curl_header in getattr(parsed_args, "headers", []):
        if curl_header.startswith(":"):
            occurrence = [m.start() for m in re.finditer(r":", curl_header)]
            header_key, header_value = curl_header[: occurrence[1]], curl_header[occurrence[1] + 1 :]
        else:
            header_key, header_value = curl_header.split(":", 1)

        if header_key.lower().strip("$") == "cookie":
            cookie = SimpleCookie(bytes(header_value, "ascii").decode("unicode-escape"))
            for key in cookie:
                cookie_dict[key] = cookie[key].value
        else:
            quoted_headers[header_key] = header_value.strip()

    # Add auth
    user = getattr(parsed_args, "user", None)
    if user:
        user = tuple(user.split(":"))

    # Add proxy and its authentication if available
    proxies = getattr(parsed_args, "proxy", None)
    if proxies and getattr(parsed_args, "proxy_user", None):
        proxies = {
            "http": f"http://{parsed_args.proxy_user}@{parsed_args.proxy}/",
            "https": f"http://{parsed_args.proxy_user}@{parsed_args.proxy}/",
        }
    elif proxies:
        proxies = {
            "http": f"http://{parsed_args.proxy}/",
            "https": f"http://{parsed_args.proxy}/",
        }

    return ParsedContext(
        method=method,
        url=getattr(parsed_args, "url", ""),  # Default to empty string if URL is missing
        data=post_data,
        headers=quoted_headers,
        cookies=cookie_dict,
        verify=getattr(parsed_args, "insecure", True),  # Default to True if missing
        auth=user,
        proxy=proxies,
    )