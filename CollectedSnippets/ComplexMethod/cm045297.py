async def _get_embedding(self, query: str) -> List[float]:
        """Generate embedding vector for the query text."""
        if not hasattr(self, "search_config"):
            raise ValueError("Host class must have a search_config attribute")

        search_config = self.search_config
        embedding_provider = getattr(search_config, "embedding_provider", None)
        embedding_model = getattr(search_config, "embedding_model", None)

        if not embedding_provider or not embedding_model:
            raise ValueError(
                "Client-side embedding is not configured. `embedding_provider` and `embedding_model` must be set."
            ) from None

        if embedding_provider.lower() == "azure_openai":
            try:
                from openai import AsyncAzureOpenAI

                from azure.identity import DefaultAzureCredential
            except ImportError:
                raise ImportError(
                    "Azure OpenAI SDK is required for client-side embedding generation. "
                    "Please install it with: uv add openai azure-identity"
                ) from None

            api_key = getattr(search_config, "openai_api_key", None)
            api_version = getattr(search_config, "openai_api_version", "2023-11-01")
            endpoint = getattr(search_config, "openai_endpoint", None)

            if not endpoint:
                raise ValueError(
                    "Azure OpenAI endpoint (`openai_endpoint`) must be provided for client-side Azure OpenAI embeddings."
                ) from None

            if api_key:
                azure_client = AsyncAzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=endpoint)
            else:

                def get_token() -> str:
                    credential = DefaultAzureCredential()
                    token = credential.get_token("https://cognitiveservices.azure.com/.default")
                    if not token or not token.token:
                        raise ValueError("Failed to acquire token using DefaultAzureCredential for Azure OpenAI.")
                    return token.token

                azure_client = AsyncAzureOpenAI(
                    azure_ad_token_provider=get_token, api_version=api_version, azure_endpoint=endpoint
                )

            try:
                response = await azure_client.embeddings.create(model=embedding_model, input=query)
                return response.data[0].embedding
            except Exception as e:
                raise ValueError(f"Failed to generate embeddings with Azure OpenAI: {str(e)}") from e

        elif embedding_provider.lower() == "openai":
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI SDK is required for client-side embedding generation. "
                    "Please install it with: uv add openai"
                ) from None

            api_key = getattr(search_config, "openai_api_key", None)
            openai_client = AsyncOpenAI(api_key=api_key)

            try:
                response = await openai_client.embeddings.create(model=embedding_model, input=query)
                return response.data[0].embedding
            except Exception as e:
                raise ValueError(f"Failed to generate embeddings with OpenAI: {str(e)}") from e
        else:
            raise ValueError(
                f"Unsupported client-side embedding provider: {embedding_provider}. "
                "Currently supported providers are 'azure_openai' and 'openai'."
            )