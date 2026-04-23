def parse_json_and_links(conn: Any) -> tuple[Any, dict[str, dict[str, str]]]:
    links = {}
    # Extract links which GH uses for pagination
    # see https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Link
    if "Link" in conn.headers:
        for elem in re.split(", *<", conn.headers["Link"]):
            try:
                url, params_ = elem.split(";", 1)
            except ValueError:
                continue
            url = urllib.parse.unquote(url.strip("<> "))
            qparams = urllib.parse.parse_qs(params_.strip(), separator=";")
            params = {
                k: v[0].strip('"')
                for k, v in qparams.items()
                if type(v) is list and len(v) > 0
            }
            params["url"] = url
            if "rel" in params:
                links[params["rel"]] = params

    return json.load(conn), links