async def test_list_models_returns_live_ollama_models_when_configured(client: AsyncClient, logged_in_headers):
    """When Ollama is configured, list_models returns live models from get_live_models_for_provider, not static list."""
    live_ollama_models = [
        {"name": "llama3.2", "icon": "Ollama", "tool_calling": True},
        {"name": "mistral", "icon": "Ollama", "tool_calling": True},
    ]

    async def mock_get_enabled_providers(*_args, **_kwargs):
        return {
            "enabled_providers": ["Ollama"],
            "provider_status": {"Ollama": True},
        }

    def mock_get_live_models(_user_id, provider, model_type="llm"):
        if provider == "Ollama" and model_type == "llm":
            return live_ollama_models
        return []

    with (
        mock.patch(
            "langflow.api.v1.models.get_enabled_providers",
            side_effect=mock_get_enabled_providers,
        ),
        mock.patch(
            "lfx.base.models.model_utils.get_live_models_for_provider",
            side_effect=mock_get_live_models,
        ),
    ):
        response = await client.get("api/v1/models", headers=logged_in_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    ollama_provider = next((p for p in data if p.get("provider") == "Ollama"), None)
    assert ollama_provider is not None
    model_names = [m["model_name"] for m in ollama_provider["models"]]
    assert set(model_names) == {"llama3.2", "mistral"}
    assert len(model_names) == 2
    assert ollama_provider["num_models"] == 2