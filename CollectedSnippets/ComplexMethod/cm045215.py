def _create_embedding_function(self) -> Any:
        """Create an embedding function based on the configuration.

        Returns:
            A ChromaDB-compatible embedding function.

        Raises:
            ValueError: If the embedding function type is unsupported.
            ImportError: If required dependencies are not installed.
        """
        try:
            from chromadb.utils import embedding_functions
        except ImportError as e:
            raise ImportError(
                "ChromaDB embedding functions not available. Ensure chromadb is properly installed."
            ) from e

        config = self._config.embedding_function_config

        if isinstance(config, DefaultEmbeddingFunctionConfig):
            return embedding_functions.DefaultEmbeddingFunction()

        elif isinstance(config, SentenceTransformerEmbeddingFunctionConfig):
            try:
                return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=config.model_name)
            except Exception as e:
                raise ImportError(
                    f"Failed to create SentenceTransformer embedding function with model '{config.model_name}'. "
                    f"Ensure sentence-transformers is installed and the model is available. Error: {e}"
                ) from e

        elif isinstance(config, OpenAIEmbeddingFunctionConfig):
            try:
                return embedding_functions.OpenAIEmbeddingFunction(api_key=config.api_key, model_name=config.model_name)
            except Exception as e:
                raise ImportError(
                    f"Failed to create OpenAI embedding function with model '{config.model_name}'. "
                    f"Ensure openai is installed and API key is valid. Error: {e}"
                ) from e

        elif isinstance(config, CustomEmbeddingFunctionConfig):
            try:
                return config.function(**config.params)
            except Exception as e:
                raise ValueError(f"Failed to create custom embedding function. Error: {e}") from e

        else:
            raise ValueError(f"Unsupported embedding function config type: {type(config)}")