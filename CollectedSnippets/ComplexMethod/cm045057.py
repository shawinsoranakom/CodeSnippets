def client(request: pytest.FixtureRequest) -> AsyncOpenAI:
    client_type = request.param

    if client_type == "mock":
        # Return a mock OpenAI client.
        return create_mock_openai_client()

    if client_type == "openai":
        # Check for OpenAI credentials in environment variables.
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            return AsyncOpenAI(api_key=openai_api_key)
        else:
            pytest.skip("OPENAI_API_KEY not set in environment variables.")

    # Check for Azure OpenAI credentials in environment variables.
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if azure_endpoint and not api_key:
        # Try Azure CLI credentials if API key not provided
        try:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
            return AsyncAzureOpenAI(
                azure_endpoint=azure_endpoint, api_version=api_version, azure_ad_token_provider=token_provider
            )
        except Exception:
            pytest.skip("Failed to obtain Azure CLI credentials.")

    if azure_endpoint and api_key:
        # Use Azure OpenAI with API key authentication.
        return AsyncAzureOpenAI(azure_endpoint=azure_endpoint, api_version=api_version, api_key=api_key)

    pytest.skip("AZURE_OPENAI_ENDPOINT not set in environment variables.")