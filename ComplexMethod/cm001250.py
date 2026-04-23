async def get_missing_items(self, batch_size: int) -> list[ContentItem]:
        """Fetch blocks without embeddings."""
        # to_thread keeps the first (heavy) call off the event loop.  On
        # subsequent calls the lru_cache makes this a dict lookup, so the
        # thread-pool overhead is negligible compared to the DB queries below.
        enabled = await asyncio.to_thread(_get_enabled_blocks)
        if not enabled:
            return []

        block_ids = list(enabled.keys())

        # Query for existing embeddings
        placeholders = ",".join([f"${i+1}" for i in range(len(block_ids))])
        existing_result = await query_raw_with_schema(
            f"""
            SELECT "contentId"
            FROM {{schema_prefix}}"UnifiedContentEmbedding"
            WHERE "contentType" = 'BLOCK'::{{schema_prefix}}"ContentType"
            AND "contentId" = ANY(ARRAY[{placeholders}])
            """,
            *block_ids,
        )

        existing_ids = {row["contentId"] for row in existing_result}

        # Convert to ContentItem — disabled filtering already done by
        # _get_enabled_blocks so batch_size won't be exhausted by disabled blocks.
        missing = ((bid, b) for bid, b in enabled.items() if bid not in existing_ids)
        items = []
        for block_id, block in itertools.islice(missing, batch_size):
            try:
                # Build searchable text from block metadata
                if not block.name:
                    logger.warning(
                        f"Block {block_id} has no name — using block_id as fallback"
                    )
                display_name = split_camelcase(block.name) if block.name else ""
                parts = []
                if display_name:
                    parts.append(display_name)
                if block.description:
                    parts.append(block.description)
                if block.categories:
                    parts.append(" ".join(str(cat.value) for cat in block.categories))

                # Add input schema field descriptions
                parts += [
                    f"{field_name}: {field_info.description}"
                    for field_name, field_info in block.input_schema.model_fields.items()
                    if field_info.description
                ]

                searchable_text = " ".join(parts)

                categories_list = (
                    [cat.value for cat in block.categories] if block.categories else []
                )

                # Extract provider names from credentials fields
                credentials_info = block.input_schema.get_credentials_fields_info()
                is_integration = len(credentials_info) > 0
                provider_names = [
                    provider.value.lower()
                    for info in credentials_info.values()
                    for provider in info.provider
                ]

                # Check if block has LlmModel field in input schema
                has_llm_model_field = any(
                    _contains_type(field.annotation, LlmModel)
                    for field in block.input_schema.model_fields.values()
                )

                items.append(
                    ContentItem(
                        content_id=block_id,
                        content_type=ContentType.BLOCK,
                        searchable_text=searchable_text,
                        metadata={
                            "name": display_name or block.name or block_id,
                            "categories": categories_list,
                            "providers": provider_names,
                            "has_llm_model_field": has_llm_model_field,
                            "is_integration": is_integration,
                        },
                        user_id=None,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to process block {block_id}: {e}")
                continue

        return items