async def test_models_endpoint_default(client: AsyncClient, logged_in_headers):
    response = await client.get("api/v1/models", headers=logged_in_headers)
    assert response.status_code == 200
    data = response.json()
    providers = {entry["provider"] for entry in data}
    assert "OpenAI" in providers
    assert "Anthropic" in providers
    assert "Google Generative AI" in providers

    for model in _flatten_models(data):
        assert model["metadata"].get("not_supported", False) is False