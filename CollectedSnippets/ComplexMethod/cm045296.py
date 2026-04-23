def validate_interdependent_fields(self) -> "AzureAISearchConfig":
        """Validate interdependent fields after all fields have been parsed."""
        if self.query_type == "semantic" and not self.semantic_config_name:
            raise ValueError("semantic_config_name must be provided when query_type is 'semantic'")

        if self.query_type == "vector" and not self.vector_fields:
            raise ValueError("vector_fields must be provided for vector search")

        if (
            self.embedding_provider
            and self.embedding_provider.lower() == "azure_openai"
            and self.embedding_model
            and not self.openai_endpoint
        ):
            raise ValueError("openai_endpoint must be provided for azure_openai embedding provider")

        return self