async def update_build_config(
        self,
        build_config: dict,
        field_value: str | dict,
        field_name: str | None = None,
    ) -> dict:
        """Update build configuration based on field name and value."""
        # Early return if no token provided
        if not self.token:
            return self.reset_build_config(build_config)

        # Database creation callback
        if field_name == "database_name" and isinstance(field_value, dict):
            if "01_new_database_name" in field_value:
                await self._create_new_database(build_config, field_value)
                return self.reset_collection_list(build_config)
            return self._update_cloud_regions(build_config, field_value)

        # Collection creation callback
        if field_name == "collection_name" and isinstance(field_value, dict):
            # Case 1: New collection creation
            if "01_new_collection_name" in field_value:
                await self._create_new_collection(build_config, field_value)
                return build_config

            # Case 2: Update embedding provider options
            if "02_embedding_generation_provider" in field_value:
                return self.reset_provider_options(build_config)

            # Case 3: Update dimension field
            if "03_embedding_generation_model" in field_value:
                return self.reset_dimension_field(build_config)

        # Initial execution or token/environment change
        first_run = field_name == "embedding_model" and not field_value and not build_config["database_name"]["options"]
        if first_run or field_name in {"token", "environment"}:
            return self.reset_database_list(build_config)

        # Database selection change
        if field_name == "database_name" and not isinstance(field_value, dict):
            return self._handle_database_selection(build_config, field_value)

        # Keyspace selection change
        if field_name == "keyspace":
            return self.reset_collection_list(build_config)

        # Collection selection change
        if field_name == "collection_name" and not isinstance(field_value, dict):
            return self._handle_collection_selection(build_config, field_value)

        return build_config