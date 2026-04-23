async def test_sagemaker_multiple_adapters_load_unload(
    async_client: openai.AsyncOpenAI,
    basic_server_with_lora: RemoteOpenAIServer,
    smollm2_lora_files,
):
    adapter_names = [f"sagemaker-adapter-{i}" for i in range(5)]

    # Load all adapters
    for adapter_name in adapter_names:
        load_response = requests.post(
            basic_server_with_lora.url_for("adapters"),
            json={"name": adapter_name, "src": smollm2_lora_files},
        )
        load_response.raise_for_status()

    # Verify all are in the models list
    models = await async_client.models.list()
    adapter_ids = [model.id for model in models.data]
    for adapter_name in adapter_names:
        assert adapter_name in adapter_ids

    # Unload all adapters
    for adapter_name in adapter_names:
        unload_response = requests.delete(
            basic_server_with_lora.url_for("adapters", adapter_name),
        )
        unload_response.raise_for_status()

    # Verify all are removed from models list
    models = await async_client.models.list()
    adapter_ids = [model.id for model in models.data]
    for adapter_name in adapter_names:
        assert adapter_name not in adapter_ids