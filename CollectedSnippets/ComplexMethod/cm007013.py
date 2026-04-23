async def update_build_config(
        self,
        build_config: dict,
        field_value: str | dict,
        field_name: str | None = None,
    ) -> dict:
        """Update build configuration with proper handling of embedding and search options."""
        # Update model options for ModelInput only when relevant.
        # Only refresh when: initial load (None), embedding_model field changes, or api_key changes.
        #
        # Note: this intentionally uses update_model_options_in_build_config directly rather than
        # handle_model_input_update because:
        #   1. The model field is named "embedding_model" (not "model"), requiring model_field_name.
        #   2. The refresh is conditional - we skip it for unrelated fields (e.g. database_name,
        #      collection_name) to avoid unnecessary work.
        #   3. AstraDB manages its own provider-field visibility (embedding_generation_provider
        #      dialog), so the generic provider-field hide/show steps in handle_model_input_update
        #      are not applicable here.
        if field_name in (None, "embedding_model", "api_key"):
            build_config = update_model_options_in_build_config(
                component=self,
                build_config=build_config,
                cache_key_prefix="embedding_model_options",
                get_options_func=get_embedding_model_options,
                field_name=field_name,
                field_value=field_value if field_name == "embedding_model" else None,
                model_field_name="embedding_model",
            )

            # Auto-populate API key based on the selected embedding model's provider.
            # Skip when user directly edits api_key to preserve their value.
            if field_name != "api_key":
                model_value = build_config.get("embedding_model", {}).get("value")
                if isinstance(model_value, list) and model_value:
                    provider = model_value[0].get("provider", "")
                    if provider:
                        build_config = apply_provider_variable_config_to_build_config(build_config, provider)

            # Ensure the API key field is always visible
            if "api_key" in build_config:
                build_config["api_key"]["show"] = True

        # Handle base astra db build config updates
        build_config = await super().update_build_config(
            build_config,
            field_value=field_value,
            field_name=field_name,
        )

        # Set embedding model display based on provider selection
        if isinstance(field_value, dict) and "02_embedding_generation_provider" in field_value:
            embedding_provider = field_value.get("02_embedding_generation_provider")
            is_custom_provider = embedding_provider and embedding_provider != "Bring your own"
            provider = embedding_provider.lower() if is_custom_provider and embedding_provider is not None else None

            build_config["embedding_model"]["show"] = not bool(provider)
            build_config["embedding_model"]["required"] = not bool(provider)

        # Early return if no API endpoint is configured
        if not self.get_api_endpoint():
            return build_config

        # Configure search method and related options
        return self._configure_search_options(build_config)