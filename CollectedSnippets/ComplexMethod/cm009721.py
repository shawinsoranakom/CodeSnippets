def _get_posts(client: Client) -> list[dict[str, Any]]:
    mock_calls = client.session.request.mock_calls  # type: ignore[attr-defined]
    posts = []
    for call in mock_calls:
        if call.args:
            if call.args[0] != "POST":
                continue
            assert call.args[0] == "POST"
            assert call.args[1].startswith("https://api.smith.langchain.com")
            body = json.loads(call.kwargs["data"])
            if "post" in body:
                # Batch request
                assert body["post"]
                posts.extend(body["post"])
            else:
                posts.append(body)
    return posts