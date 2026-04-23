async def search_custom_secrets(
    name__contains: Annotated[
        str | None,
        Query(title='Filter by name containing this string'),
    ] = None,
    page_id: Annotated[
        str | None,
        Query(title='Optional next_page_id from the previously returned page'),
    ] = None,
    limit: Annotated[
        int,
        Query(
            title='The max number of results in the page',
            gt=0,
            le=100,
        ),
    ] = 100,
    user_secrets: Secrets | None = Depends(get_secrets),
) -> CustomSecretPage:
    """Search / List custom secrets.

    Retrieves the names and descriptions of custom secrets for the authenticated user.
    Results are paginated and can be filtered by name.

    Returns:
        CustomSecretPage: Paginated list of custom secrets (without values)
    """
    if not user_secrets or not user_secrets.custom_secrets:
        return CustomSecretPage(items=[], next_page_id=None)

    # Build list of all secrets, optionally filtered by name
    all_secrets: list[CustomSecretWithoutValue] = []
    for secret_name, secret_value in sorted(user_secrets.custom_secrets.items()):
        if name__contains and name__contains.lower() not in secret_name.lower():
            continue
        all_secrets.append(
            CustomSecretWithoutValue(
                name=secret_name,
                description=secret_value.description,
            )
        )

    # Apply pagination
    start_index = 0
    if page_id:
        # Find the index after the page_id secret
        for i, secret in enumerate(all_secrets):
            if secret.name == page_id:
                start_index = i + 1
                break

    # Get the page of results
    end_index = start_index + limit
    page_items = all_secrets[start_index:end_index]

    # Determine next_page_id
    next_page_id = None
    if end_index < len(all_secrets):
        next_page_id = page_items[-1].name if page_items else None

    return CustomSecretPage(items=page_items, next_page_id=next_page_id)