def create_citation(
    *,
    url: str | None = None,
    title: str | None = None,
    start_index: int | None = None,
    end_index: int | None = None,
    cited_text: str | None = None,
    id: str | None = None,
    **kwargs: Any,
) -> Citation:
    """Create a `Citation`.

    Args:
        url: URL of the document source.
        title: Source document title.
        start_index: Start index in the response text where citation applies.
        end_index: End index in the response text where citation applies.
        cited_text: Excerpt of source text being cited.
        id: Content block identifier.

            Generated automatically if not provided.

    Returns:
        A properly formatted `Citation`.

    !!! note

        The `id` is generated automatically if not provided, using a UUID4 format
        prefixed with `'lc_'` to indicate it is a LangChain-generated ID.
    """
    block = Citation(type="citation", id=ensure_id(id))

    if url is not None:
        block["url"] = url
    if title is not None:
        block["title"] = title
    if start_index is not None:
        block["start_index"] = start_index
    if end_index is not None:
        block["end_index"] = end_index
    if cited_text is not None:
        block["cited_text"] = cited_text

    extras = {k: v for k, v in kwargs.items() if v is not None}
    if extras:
        block["extras"] = extras

    return block