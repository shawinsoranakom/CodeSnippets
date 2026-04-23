def get_provider_icon(cls, collection=None, provider_name: str | None = None) -> str:
        # Get the provider name from the collection
        provider_name = provider_name or (
            collection.definition.vector.service.provider
            if (
                collection
                and collection.definition
                and collection.definition.vector
                and collection.definition.vector.service
            )
            else None
        )

        # If there is no provider, use the vector store icon
        if not provider_name or provider_name.lower() == "bring your own":
            return "vectorstores"

        # Map provider casings
        case_map = {
            "nvidia": "NVIDIA",
            "openai": "OpenAI",
            "amazon bedrock": "AmazonBedrockEmbeddings",
            "azure openai": "AzureOpenAiEmbeddings",
            "cohere": "Cohere",
            "jina ai": "JinaAI",
            "mistral ai": "MistralAI",
            "upstage": "Upstage",
            "voyage ai": "VoyageAI",
        }

        # Adjust the casing on some like nvidia
        return case_map[provider_name.lower()] if provider_name.lower() in case_map else provider_name.title()