def slugify(text: str) -> str:
    return py_slugify(
        text,
        replacements=[
            ("`", ""),  # `dict`s -> dicts
            ("'s", "s"),  # it's -> its
            ("'t", "t"),  # don't -> dont
            ("**", ""),  # **FastAPI**s -> FastAPIs
        ],
    )