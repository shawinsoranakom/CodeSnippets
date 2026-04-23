def custom_generate_unique_id(route: APIRoute):
    """Generate clean operation IDs for OpenAPI spec following the format:
    {method}{tag}{summary}
    """
    if not route.tags or not route.methods:
        return f"{route.name}"

    method = list(route.methods)[0].lower()
    first_tag = route.tags[0]
    if isinstance(first_tag, Enum):
        tag_str = first_tag.name
    else:
        tag_str = str(first_tag)

    tag = "".join(word.capitalize() for word in tag_str.split("_"))  # v1/v2

    summary = (
        route.summary if route.summary else route.name
    )  # need to be unique, a different version could have the same summary
    summary = "".join(word.capitalize() for word in str(summary).split("_"))

    if tag:
        return f"{method}{tag}{summary}"
    else:
        return f"{method}{summary}"