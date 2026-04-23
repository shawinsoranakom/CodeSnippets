def fix_ai_model_parameter(
        self,
        agent: AgentDict,
        blocks: list[dict[str, Any]],
        default_model: str = "gpt-4o",
    ) -> AgentDict:
        """
        Add or fix the model parameter on AI blocks.

        For nodes whose block has category "AI", this function ensures that the
        input_default has a "model" parameter set to one of the allowed models.
        If missing or set to an unsupported value, it is replaced with the
        appropriate default.

        Blocks that define their own ``enum`` constraint on the ``model`` field
        in their inputSchema (e.g. PerplexityBlock) are validated against that
        enum instead of the generic allowed set.

        Args:
            agent: The agent dictionary to fix
            blocks: List of available blocks with their schemas
            default_model: The fallback model to use (default "gpt-4o")

        Returns:
            The fixed agent dictionary
        """
        generic_allowed_models = {"gpt-4o", "claude-opus-4-6"}

        # Create a mapping of block_id to block for quick lookup
        block_map = {block.get("id"): block for block in blocks}

        nodes = agent.get("nodes", [])
        fixed_count = 0

        for node in nodes:
            block_id = node.get("block_id")
            block = block_map.get(block_id)

            if not block:
                continue

            # Check if the block has category "AI" in its categories array
            categories = block.get("categories", [])
            is_ai_block = any(
                cat.get("category") == "AI"
                for cat in categories
                if isinstance(cat, dict)
            )

            if is_ai_block:
                # Skip AI blocks that don't expose a "model" input property
                # (some AI-category blocks have no model selector at all).
                input_properties = block.get("inputSchema", {}).get("properties", {})
                if "model" not in input_properties:
                    continue

                node_id = node.get("id")
                input_default = node.get("input_default", {})
                current_model = input_default.get("model")

                # Determine allowed models and default from the block's schema.
                # Blocks with a block-specific enum on the model field (e.g.
                # PerplexityBlock) use their own enum values; others use the
                # generic set.
                model_schema = input_properties.get("model", {})
                block_model_enum = model_schema.get("enum")

                if block_model_enum:
                    allowed_models = set(block_model_enum)
                    fallback_model = model_schema.get("default", block_model_enum[0])
                else:
                    allowed_models = generic_allowed_models
                    fallback_model = default_model

                if current_model not in allowed_models:
                    block_name = block.get("name", "Unknown AI Block")
                    if current_model is None:
                        self.add_fix_log(
                            f"Added model parameter '{fallback_model}' to AI "
                            f"block node {node_id} ({block_name})"
                        )
                    else:
                        self.add_fix_log(
                            f"Replaced unsupported model '{current_model}' "
                            f"with '{fallback_model}' on AI block node "
                            f"{node_id} ({block_name})"
                        )
                    input_default["model"] = fallback_model
                    node["input_default"] = input_default
                    fixed_count += 1

        if fixed_count > 0:
            logger.debug(f"Fixed model parameter on {fixed_count} AI block nodes")

        return agent