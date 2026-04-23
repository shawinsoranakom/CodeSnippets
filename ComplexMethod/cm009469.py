def mustache_schema(template: str) -> type[BaseModel]:
    """Get the variables from a mustache template.

    Args:
        template: The template string.

    Returns:
        The variables from the template as a Pydantic model.
    """
    fields = {}
    prefix: tuple[str, ...] = ()
    section_stack: list[tuple[str, ...]] = []
    for type_, key in mustache.tokenize(template):
        if key == ".":
            continue
        if type_ == "end":
            if section_stack:
                prefix = section_stack.pop()
        elif type_ in {"section", "inverted section"}:
            section_stack.append(prefix)
            prefix += tuple(key.split("."))
            fields[prefix] = False
        elif type_ in {"variable", "no escape"}:
            fields[prefix + tuple(key.split("."))] = True

    for fkey, fval in fields.items():
        fields[fkey] = fval and not any(
            is_subsequence(fkey, k) for k in fields if k != fkey
        )
    defs: Defs = {}  # None means leaf node
    while fields:
        field, is_leaf = fields.popitem()
        current = defs
        for part in field[:-1]:
            current = current.setdefault(part, {})
        current.setdefault(field[-1], "" if is_leaf else {})  # type: ignore[arg-type]
    return _create_model_recursive("PromptInput", defs)