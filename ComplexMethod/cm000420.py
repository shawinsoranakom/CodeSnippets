def _json_to_themed_prompts(value: Any) -> dict[str, list[str]]:
    """Convert Json field to themed prompts dict.

    Handles both the new ``dict[str, list[str]]`` format and the legacy
    ``list[str]`` format.  Legacy rows are placed under a ``"General"`` key so
    existing personalised prompts remain readable until a backfill regenerates
    them into the proper themed shape.
    """
    if isinstance(value, dict):
        return {
            k: [i for i in v if isinstance(i, str)]
            for k, v in value.items()
            if isinstance(k, str) and isinstance(v, list)
        }
    if isinstance(value, list) and value:
        return {"General": [str(p) for p in value if isinstance(p, str)]}
    return {}