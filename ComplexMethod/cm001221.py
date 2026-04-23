async def _text_search_blocks(
    *,
    query: str,
    include_blocks: bool,
    include_integrations: bool,
) -> tuple[list[_ScoredItem], int, int]:
    """
    Search blocks using in-memory text matching over the block registry.

    All blocks are already loaded in memory, so this is fast and reliable
    regardless of whether OpenAI embeddings are available.

    Scoring:
        - Base: text relevance via _score_primary_fields, plus BLOCK_SCORE_BOOST
          to prioritize blocks over marketplace agents in combined results
        - +20 if the block has an LlmModel field and the query matches an LLM model name
    """
    results: list[_ScoredItem] = []

    if not include_blocks and not include_integrations:
        return results, 0, 0

    normalized_query = query.strip().lower()

    all_results, _, _ = _collect_block_results(
        include_blocks=include_blocks,
        include_integrations=include_integrations,
    )

    all_blocks = load_all_blocks()

    for item in all_results:
        block_info = item.item
        assert isinstance(block_info, BlockInfo)
        name = split_camelcase(block_info.name).lower()

        # Build rich description including input field descriptions,
        # matching the searchable text that the embedding pipeline uses
        desc_parts = [block_info.description or ""]
        block_cls = all_blocks.get(block_info.id)
        if block_cls is not None:
            block: AnyBlockSchema = block_cls()
            desc_parts += [
                f"{f}: {info.description}"
                for f, info in block.input_schema.model_fields.items()
                if info.description
            ]
        description = " ".join(desc_parts).lower()

        score = _score_primary_fields(name, description, normalized_query)

        # Add LLM model match bonus
        if block_cls is not None and _matches_llm_model(
            block_cls().input_schema, normalized_query
        ):
            score += 20

        if score >= MIN_SCORE_FOR_FILTERED_RESULTS:
            results.append(
                _ScoredItem(
                    item=block_info,
                    filter_type=item.filter_type,
                    score=score + BLOCK_SCORE_BOOST,
                    sort_key=name,
                )
            )

    block_count = sum(1 for r in results if r.filter_type == "blocks")
    integration_count = sum(1 for r in results if r.filter_type == "integrations")
    return results, block_count, integration_count