async def test_stream_options(foscolo, server):
    server, model_name = server
    url = server.url_for("v1/audio/translations")
    headers = {"Authorization": f"Bearer {server.DUMMY_API_KEY}"}
    data = {
        "model": model_name,
        "language": "it",
        "to_language": "en",
        "stream": True,
        "stream_include_usage": True,
        "stream_continuous_usage_stats": True,
        "temperature": 0.0,
    }
    foscolo.seek(0)
    final = False
    continuous = True
    async with httpx.AsyncClient() as http_client:
        files = {"file": foscolo}
        async with http_client.stream(
            "POST", url, headers=headers, data=data, files=files
        ) as response:
            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    line = line[len("data: ") :]
                if line.strip() == "[DONE]":
                    break
                chunk = json.loads(line)
                choices = chunk.get("choices", [])
                if not choices:
                    # final usage sent
                    final = True
                else:
                    continuous = continuous and ("usage" in chunk)
    assert final and continuous