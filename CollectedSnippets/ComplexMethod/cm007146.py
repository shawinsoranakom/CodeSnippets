def _get_embedding_model_name(self, embedding_obj=None) -> str:
        """Get the embedding model name from component config or embedding object.

        Priority: deployment > model > model_id > model_name
        This ensures we use the actual model being deployed, not just the configured model.
        Supports multiple embedding providers (OpenAI, Watsonx, Cohere, etc.)

        Args:
            embedding_obj: Specific embedding object to get name from (optional)

        Returns:
            Embedding model name

        Raises:
            ValueError: If embedding model name cannot be determined
        """
        # First try explicit embedding_model_name input
        if hasattr(self, "embedding_model_name") and self.embedding_model_name:
            return self.embedding_model_name.strip()

        # Try to get from provided embedding object
        if embedding_obj:
            # Priority: deployment > model > model_id > model_name
            if hasattr(embedding_obj, "deployment") and embedding_obj.deployment:
                return str(embedding_obj.deployment)
            if hasattr(embedding_obj, "model") and embedding_obj.model:
                return str(embedding_obj.model)
            if hasattr(embedding_obj, "model_id") and embedding_obj.model_id:
                return str(embedding_obj.model_id)
            if hasattr(embedding_obj, "model_name") and embedding_obj.model_name:
                return str(embedding_obj.model_name)

        # Try to get from embedding component (legacy single embedding)
        if hasattr(self, "embedding") and self.embedding:
            # Handle list of embeddings
            if isinstance(self.embedding, list) and len(self.embedding) > 0:
                first_emb = self.embedding[0]
                if hasattr(first_emb, "deployment") and first_emb.deployment:
                    return str(first_emb.deployment)
                if hasattr(first_emb, "model") and first_emb.model:
                    return str(first_emb.model)
                if hasattr(first_emb, "model_id") and first_emb.model_id:
                    return str(first_emb.model_id)
                if hasattr(first_emb, "model_name") and first_emb.model_name:
                    return str(first_emb.model_name)
            # Handle single embedding
            elif not isinstance(self.embedding, list):
                if hasattr(self.embedding, "deployment") and self.embedding.deployment:
                    return str(self.embedding.deployment)
                if hasattr(self.embedding, "model") and self.embedding.model:
                    return str(self.embedding.model)
                if hasattr(self.embedding, "model_id") and self.embedding.model_id:
                    return str(self.embedding.model_id)
                if hasattr(self.embedding, "model_name") and self.embedding.model_name:
                    return str(self.embedding.model_name)

        msg = (
            "Could not determine embedding model name. "
            "Please set the 'embedding_model_name' field or ensure the embedding component "
            "has a 'deployment', 'model', 'model_id', or 'model_name' attribute."
        )
        raise ValueError(msg)