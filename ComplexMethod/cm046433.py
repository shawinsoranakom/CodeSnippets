def repo_slug_from_source(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    normalized = normalized.removesuffix(".git")
    if normalized.startswith("https://github.com/"):
        slug = normalized[len("https://github.com/") :]
    elif normalized.startswith("http://github.com/"):
        slug = normalized[len("http://github.com/") :]
    elif normalized.startswith("git@github.com:"):
        slug = normalized[len("git@github.com:") :]
    else:
        slug = normalized
    slug = slug.strip("/")
    parts = slug.split("/")
    if len(parts) != 2 or not all(parts):
        return None
    return f"{parts[0]}/{parts[1]}"