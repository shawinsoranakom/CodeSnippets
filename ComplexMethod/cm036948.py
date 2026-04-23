async def test_metrics_exist(
    local_asset_server: LocalAssetServer,
    server: RemoteOpenAIServer,
    client: openai.AsyncClient,
    model_key: str,
):
    model_name = MODELS[model_key]

    # sending a request triggers the metrics to be logged.
    if model_key == "text":
        await client.completions.create(
            model=model_name,
            prompt="Hello, my name is",
            max_tokens=5,
            temperature=0.0,
        )
    else:
        # https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg
        await client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": local_asset_server.url_for(
                                    "2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
                                ),
                            },
                        },
                        {"type": "text", "text": "What's in this image?"},
                    ],
                }
            ],
            max_tokens=5,
            temperature=0.0,
        )

    response = requests.get(server.url_for("metrics"))
    assert response.status_code == HTTPStatus.OK

    expected_metrics = EXPECTED_METRICS_V1
    if model_key == "multimodal":
        # NOTE: Don't use in-place assignment
        expected_metrics = expected_metrics + EXPECTED_METRICS_MM

    for metric in expected_metrics:
        if metric in HIDDEN_DEPRECATED_METRICS and not server.show_hidden_metrics:
            continue
        assert metric in response.text