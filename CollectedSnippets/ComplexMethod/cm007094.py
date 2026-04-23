async def update_build_config(
        self,
        build_config,
        field_value: Any,
        field_name: str | None = None,
    ):
        """Update build configuration based on provider selection."""
        # Check if we're in Astra cloud environment and raise an error if we are.
        raise_error_if_astra_cloud_disable_component(astra_error_msg)

        # Populate the dialog's embedding model options so the ModelInput renders correctly
        try:
            dialog_template = (
                build_config["knowledge_base"]
                .get("dialog_inputs", {})
                .get("fields", {})
                .get("data", {})
                .get("node", {})
                .get("template", {})
            )
            if "02_embedding_model" in dialog_template:
                embedding_options = get_embedding_model_options(user_id=self.user_id)
                dialog_template["02_embedding_model"]["options"] = embedding_options
        except Exception:  # noqa: BLE001
            self.log("Failed to populate embedding model options in dialog")

        # Create a new knowledge base
        if field_name == "knowledge_base":
            async with session_scope() as db:
                if not self.user_id:
                    msg = "User ID is required for fetching knowledge base list."
                    raise ValueError(msg)
                current_user = await get_user_by_id(db, self.user_id)
                if not current_user:
                    msg = f"User with ID {self.user_id} not found."
                    raise ValueError(msg)
                kb_user = current_user.username
            if isinstance(field_value, dict) and "01_new_kb_name" in field_value:
                # Validate the knowledge base name - Make sure it follows these rules:
                if not self.is_valid_collection_name(field_value["01_new_kb_name"]):
                    msg = f"Invalid knowledge base name: {field_value['01_new_kb_name']}"
                    raise ValueError(msg)

                # The model selection comes from ModelInput as a list of dicts
                model_selection = field_value["02_embedding_model"]
                if isinstance(model_selection, dict):
                    model_selection = [model_selection]

                # Build and validate the embedding model via the shared utility
                embed_model = get_embeddings(
                    model=model_selection,
                    user_id=self.user_id,
                )

                # Try to generate a dummy embedding to validate without blocking the event loop
                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(embed_model.embed_query, "test"),
                        timeout=10,
                    )
                except TimeoutError as e:
                    msg = "Embedding validation timed out. Please verify network connectivity and key."
                    raise ValueError(msg) from e
                except Exception as e:
                    msg = f"Embedding validation failed: {e!s}"
                    raise ValueError(msg) from e

                # Create the new knowledge base directory
                kb_path = _get_knowledge_bases_root_path() / kb_user / field_value["01_new_kb_name"]
                kb_path.mkdir(parents=True, exist_ok=True)

                # Save the embedding metadata
                build_config["knowledge_base"]["value"] = field_value["01_new_kb_name"]
                self._save_embedding_metadata(
                    kb_path=kb_path,
                    model_selection=model_selection,
                )

            # Update the knowledge base options dynamically
            build_config["knowledge_base"]["options"] = await get_knowledge_bases(
                _get_knowledge_bases_root_path(),
                user_id=self.user_id,
            )

            # If the selected knowledge base is not available, reset it
            if build_config["knowledge_base"]["value"] not in build_config["knowledge_base"]["options"]:
                build_config["knowledge_base"]["value"] = None

        return build_config