def get_graphql_response(
    *,
    settings: Settings,
    query: str,
    after: str | None = None,
    category_id: str | None = None,
    discussion_number: int | None = None,
    discussion_id: str | None = None,
    comment_id: str | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    headers = {"Authorization": f"token {settings.github_token.get_secret_value()}"}
    variables = {
        "after": after,
        "category_id": category_id,
        "discussion_number": discussion_number,
        "discussion_id": discussion_id,
        "comment_id": comment_id,
        "body": body,
    }
    response = httpx.post(
        github_graphql_url,
        headers=headers,
        timeout=settings.httpx_timeout,
        json={"query": query, "variables": variables, "operationName": "Q"},
    )
    if response.status_code != 200:
        logging.error(
            f"Response was not 200, after: {after}, category_id: {category_id}"
        )
        logging.error(response.text)
        raise RuntimeError(response.text)
    data = response.json()
    if "errors" in data:
        logging.error(f"Errors in response, after: {after}, category_id: {category_id}")
        logging.error(data["errors"])
        logging.error(response.text)
        raise RuntimeError(response.text)
    return cast(dict[str, Any], data)