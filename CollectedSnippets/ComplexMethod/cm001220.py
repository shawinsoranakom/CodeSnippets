def _collect_block_results(
    *,
    include_blocks: bool,
    include_integrations: bool,
) -> tuple[list[_ScoredItem], int, int]:
    """
    Collect all blocks for listing (no search query).

    All blocks get BLOCK_SCORE_BOOST to prioritize them over marketplace agents.
    """
    results: list[_ScoredItem] = []
    block_count = 0
    integration_count = 0

    if not include_blocks and not include_integrations:
        return results, block_count, integration_count

    for block_type in load_all_blocks().values():
        block: AnyBlockSchema = block_type()
        if block.disabled:
            continue

        # Skip excluded blocks
        if block.id in EXCLUDED_BLOCK_IDS:
            continue

        block_info = block.get_info()
        credentials = list(block.input_schema.get_credentials_fields().values())
        is_integration = len(credentials) > 0

        if is_integration and not include_integrations:
            continue
        if not is_integration and not include_blocks:
            continue

        filter_type: FilterType = "integrations" if is_integration else "blocks"
        if is_integration:
            integration_count += 1
        else:
            block_count += 1

        results.append(
            _ScoredItem(
                item=block_info,
                filter_type=filter_type,
                score=BLOCK_SCORE_BOOST,
                sort_key=block_info.name.lower(),
            )
        )

    return results, block_count, integration_count