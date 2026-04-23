async def _build_embeddings(provider: str, model: str, current_user):
        """Internal helper to build embeddings object."""
        options = get_embedding_model_options(user_id=current_user.id)
        selected_option = next((o for o in options if o["provider"] == provider and o["name"] == model), None)

        if not selected_option:
            all_options = get_embedding_model_options()
            selected_option = next((o for o in all_options if o["provider"] == provider and o["name"] == model), None)

            if not selected_option:
                msg = f"Embedding model '{model}' for provider '{provider}' not found."
                raise ValueError(msg)

        embedding_model = EmbeddingModelComponent(model=[selected_option], _user_id=current_user.id)
        return embedding_model.build_embeddings()