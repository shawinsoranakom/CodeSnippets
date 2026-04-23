def gh_fetch_url_and_headers(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    data: dict[str, Any] | None | str = None,
    method: str | None = None,
    reader: Callable[[Any], Any] = lambda x: x.read(),
) -> tuple[Any, Any]:
    if headers is None:
        headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token is not None and url.startswith(f"{GITHUB_API_URL}/"):
        headers["Authorization"] = f"token {token}"

    data_ = None
    if data is not None:
        data_ = data.encode() if isinstance(data, str) else json.dumps(data).encode()

    try:
        with urlopen(Request(url, headers=headers, data=data_, method=method)) as conn:
            return conn.headers, reader(conn)
    except HTTPError as err:
        if (
            err.code == 403
            and all(
                key in err.headers
                for key in ["X-RateLimit-Limit", "X-RateLimit-Remaining"]
            )
            and int(err.headers["X-RateLimit-Remaining"]) == 0
        ):
            print(
                f"""{url}
                Rate limit exceeded:
                Used: {err.headers["X-RateLimit-Used"]}
                Limit: {err.headers["X-RateLimit-Limit"]}
                Remaining: {err.headers["X-RateLimit-Remaining"]}
                Resets at: {err.headers["x-RateLimit-Reset"]}"""
            )
        else:
            print(f"Error fetching {url} {err}")
        raise