async def search_models(
    page_id: Annotated[
        str | None,
        Query(title='Optional next_page_id from the previously returned page'),
    ] = None,
    limit: Annotated[
        int,
        Query(title='The max number of results in the page', gt=0, le=100),
    ] = 50,
    query: Annotated[
        str | None,
        Query(title='Filter models by name (case-insensitive substring match)'),
    ] = None,
    verified__eq: Annotated[
        bool | None,
        Query(title='Filter by verified status (true/false, omit for all)'),
    ] = None,
    provider__eq: Annotated[
        str | None,
        Query(title='Filter by provider name (exact match)'),
    ] = None,
    models: ModelsResponse = Depends(get_llm_models_dependency),
) -> LLMModelPage:
    """Search for LLM models with pagination and filtering.

    Returns a paginated list of models that can be filtered by name
    (contains), verified status, and provider.
    """
    filtered_models = _get_all_models_with_verified(models)

    if query is not None:
        query_lower = query.lower()
        filtered_models = [m for m in filtered_models if query_lower in m.name.lower()]

    if verified__eq is not None:
        filtered_models = [m for m in filtered_models if m.verified == verified__eq]

    if provider__eq is not None:
        filtered_models = [m for m in filtered_models if m.provider == provider__eq]

    # Apply pagination
    items, next_page_id = paginate_results(filtered_models, page_id, limit)

    return LLMModelPage(items=items, next_page_id=next_page_id)