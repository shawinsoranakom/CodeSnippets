def _validate_config(
        cls, config_dict: Dict[str, Any], search_type: Literal["full_text", "vector", "hybrid"]
    ) -> None:
        """Validate configuration for specific search types."""
        credential = config_dict.get("credential")
        if isinstance(credential, str):
            raise TypeError("Credential must be AzureKeyCredential, AsyncTokenCredential, or a valid dict")
        if isinstance(credential, dict) and "api_key" not in credential:
            raise ValueError("If credential is a dict, it must contain an 'api_key' key")

        try:
            _ = AzureAISearchConfig(**config_dict)
        except Exception as e:
            raise ValueError(f"Invalid configuration: {str(e)}") from e

        if search_type == "vector":
            vector_fields = config_dict.get("vector_fields")
            if not vector_fields or len(vector_fields) == 0:
                raise ValueError("vector_fields must contain at least one field name for vector search")

        elif search_type == "hybrid":
            vector_fields = config_dict.get("vector_fields")
            search_fields = config_dict.get("search_fields")

            if not vector_fields or len(vector_fields) == 0:
                raise ValueError("vector_fields must contain at least one field name for hybrid search")

            if not search_fields or len(search_fields) == 0:
                raise ValueError("search_fields must contain at least one field name for hybrid search")