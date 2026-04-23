def from_ui_selection(
        cls,
        dropdown_value: Optional[str],
        search_value: Optional[str],
        local_models: list = None,
        hf_token: Optional[str] = None,
        is_lora: bool = False,
    ) -> Optional["ModelConfig"]:
        """
        Create a universal ModelConfig from UI dropdown/search selections.
        Handles base models and LoRA adapters.
        """
        selected = None
        if search_value and search_value.strip():
            selected = search_value.strip()
        elif dropdown_value:
            selected = dropdown_value

        if not selected:
            return None

        display_name = selected

        #  Use the correct 'local_models' parameter to resolve display names
        if " (Active)" in selected or " (Ready)" in selected:
            clean_display_name = selected.replace(" (Active)", "").replace(
                " (Ready)", ""
            )
            if local_models:
                for local_display, local_path in local_models:
                    if local_display == clean_display_name:
                        selected = local_path
                        break

        # Clean all UI status indicators to get the final identifier
        identifier = selected
        for status in UI_STATUS_INDICATORS:
            identifier = identifier.replace(status, "")
        identifier = identifier.strip()

        is_local = is_local_path(identifier)
        path = normalize_path(identifier) if is_local else identifier

        # Add unsloth/ prefix for shorthand HF models
        if not is_local and "/" not in identifier:
            identifier = f"unsloth/{identifier}"
            path = identifier

        if not is_local:
            resolved_identifier = resolve_cached_repo_id_case(identifier)
            if resolved_identifier != identifier:
                identifier = resolved_identifier
                path = resolved_identifier

        # --- Logic for Base Model and Vision Detection ---
        base_model = None
        is_vision = False

        if is_lora:
            # For a LoRA, we MUST find its base model.
            base_model = get_base_model_from_lora(path)
            if not base_model:
                logger.warning(
                    f"Could not determine base model for LoRA '{path}'. Cannot create config."
                )
                return None  # Cannot proceed without a base model

            # A LoRA's vision capability is determined by its base model.
            is_vision = is_vision_model(base_model, hf_token = hf_token)
        else:
            # For a base model, just check its own vision status.
            is_vision = is_vision_model(identifier, hf_token = hf_token)

        from utils.paths import is_model_cached

        is_cached = is_model_cached(identifier) if not is_local else True

        return cls(
            identifier = identifier,
            display_name = display_name,
            path = path,
            is_local = is_local,
            is_cached = is_cached,
            is_vision = is_vision,
            is_lora = is_lora,
            base_model = base_model,  # This will be None for base models, and populated for LoRAs
        )