def parse_curl_command(curl_command):
    tokens = shlex.split(normalize_newlines(curl_command))
    tokens = [token for token in tokens if token and token != " "]
    if tokens and "curl" not in tokens[0]:
        msg = "Invalid curl command"
        raise ValueError(msg)
    args_template = {
        "command": None,
        "url": None,
        "data": None,
        "data_binary": None,
        "method": "get",
        "headers": [],
        "compressed": False,
        "insecure": False,
        "user": (),
        "include": False,
        "silent": False,
        "proxy": None,
        "proxy_user": None,
        "cookies": {},
    }
    args = args_template.copy()
    method_on_curl = None
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "-X":
            i += 1
            args["method"] = tokens[i].lower()
            method_on_curl = tokens[i].lower()
        elif token in {"-d", "--data"}:
            i += 1
            args["data"] = tokens[i]
        elif token in {"-b", "--data-binary", "--data-raw"}:
            i += 1
            args["data_binary"] = tokens[i]
        elif token in {"-H", "--header"}:
            i += 1
            args["headers"].append(tokens[i])
        elif token == "--compressed":
            args["compressed"] = True
        elif token in {"-k", "--insecure"}:
            args["insecure"] = True
        elif token in {"-u", "--user"}:
            i += 1
            args["user"] = tuple(tokens[i].split(":"))
        elif token in {"-I", "--include"}:
            args["include"] = True
        elif token in {"-s", "--silent"}:
            args["silent"] = True
        elif token in {"-x", "--proxy"}:
            i += 1
            args["proxy"] = tokens[i]
        elif token in {"-U", "--proxy-user"}:
            i += 1
            args["proxy_user"] = tokens[i]
        elif not token.startswith("-"):
            if args["command"] is None:
                args["command"] = token
            else:
                args["url"] = token
        i += 1

    args["method"] = method_on_curl or args["method"]

    return ParsedArgs(**args)