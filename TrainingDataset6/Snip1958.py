def get_graphql_response(
    *,
    settings: Settings,
    query: str,
    after: str | None = None,
) -> dict[str, Any]:
    headers = {"Authorization": f"token {settings.sponsors_token.get_secret_value()}"}
    variables = {"after": after}
    response = httpx.post(
        github_graphql_url,
        headers=headers,
        timeout=settings.httpx_timeout,
        json={"query": query, "variables": variables, "operationName": "Q"},
    )
    if response.status_code != 200:
        logging.error(f"Response was not 200, after: {after}")
        logging.error(response.text)
        raise RuntimeError(response.text)
    data = response.json()
    if "errors" in data:
        logging.error(f"Errors in response, after: {after}")
        logging.error(data["errors"])
        logging.error(response.text)
        raise RuntimeError(response.text)
    return data