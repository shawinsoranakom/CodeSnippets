def _score_block(
    block: AnyBlockSchema,
    block_info: BlockInfo,
    normalized_query: str,
) -> float:
    if not normalized_query:
        return 0.0

    name = block_info.name.lower()
    description = block_info.description.lower()
    score = _score_primary_fields(name, description, normalized_query)

    category_text = " ".join(
        category.get("category", "").lower() for category in block_info.categories
    )
    score += _score_additional_field(category_text, normalized_query, 12, 6)

    credentials_info = block.input_schema.get_credentials_fields_info().values()
    provider_names = [
        provider.value.lower()
        for info in credentials_info
        for provider in info.provider
    ]
    provider_text = " ".join(provider_names)
    score += _score_additional_field(provider_text, normalized_query, 15, 6)

    if _matches_llm_model(block.input_schema, normalized_query):
        score += 20

    return score
