def _execute_paginated_retrieval(
    retrieval_function: Callable,
    list_key: str | None = None,
    continue_on_404_or_403: bool = False,
    max_num_pages: int | None = None,
    **kwargs: Any,
) -> Iterator[GoogleDriveFileType | str]:
    """Execute a paginated retrieval from Google Drive API
    Args:
        retrieval_function: The specific list function to call (e.g., service.files().list)
        list_key: If specified, each object returned by the retrieval function
                  will be accessed at the specified key and yielded from.
        continue_on_404_or_403: If True, the retrieval will continue even if the request returns a 404 or 403 error.
        max_num_pages: If specified, the retrieval will stop after the specified number of pages and yield None.
        **kwargs: Arguments to pass to the list function
    """
    if "fields" not in kwargs or "nextPageToken" not in kwargs["fields"]:
        raise ValueError("fields must contain nextPageToken for execute_paginated_retrieval")
    next_page_token = kwargs.get(PAGE_TOKEN_KEY, "")
    num_pages = 0
    while next_page_token is not None:
        if max_num_pages is not None and num_pages >= max_num_pages:
            yield next_page_token
            return
        num_pages += 1
        request_kwargs = kwargs.copy()
        if next_page_token:
            request_kwargs[PAGE_TOKEN_KEY] = next_page_token
        results = _execute_single_retrieval(
            retrieval_function,
            continue_on_404_or_403,
            **request_kwargs,
        )

        next_page_token = results.get(NEXT_PAGE_TOKEN_KEY)
        if list_key:
            for item in results.get(list_key, []):
                yield item
        else:
            yield results