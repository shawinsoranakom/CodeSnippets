def test_azure_config(config_with_azure: AppConfig) -> None:
    assert (credentials := config_with_azure.openai_credentials) is not None
    assert credentials.api_type == SecretStr("azure")
    assert credentials.api_version == SecretStr("2023-06-01-preview")
    assert credentials.azure_endpoint == SecretStr("https://dummy.openai.azure.com")
    assert credentials.azure_model_to_deploy_id_map == {
        config_with_azure.fast_llm: "FAST-LLM_ID",
        config_with_azure.smart_llm: "SMART-LLM_ID",
        config_with_azure.embedding_model: "embedding-deployment-id-for-azure",
    }

    fast_llm = config_with_azure.fast_llm
    smart_llm = config_with_azure.smart_llm
    assert (
        credentials.get_model_access_kwargs(config_with_azure.fast_llm)["model"]
        == "FAST-LLM_ID"
    )
    assert (
        credentials.get_model_access_kwargs(config_with_azure.smart_llm)["model"]
        == "SMART-LLM_ID"
    )

    # Emulate --gpt4only
    config_with_azure.fast_llm = smart_llm
    assert (
        credentials.get_model_access_kwargs(config_with_azure.fast_llm)["model"]
        == "SMART-LLM_ID"
    )
    assert (
        credentials.get_model_access_kwargs(config_with_azure.smart_llm)["model"]
        == "SMART-LLM_ID"
    )

    # Emulate --gpt3only
    config_with_azure.fast_llm = config_with_azure.smart_llm = fast_llm
    assert (
        credentials.get_model_access_kwargs(config_with_azure.fast_llm)["model"]
        == "FAST-LLM_ID"
    )
    assert (
        credentials.get_model_access_kwargs(config_with_azure.smart_llm)["model"]
        == "FAST-LLM_ID"
    )