def infer_source_ref_kind(ref: str | None) -> str:
    if not isinstance(ref, str):
        return "tag"
    normalized = ref.strip()
    lowered = normalized.lower()
    if not normalized:
        return "tag"
    if lowered.startswith("refs/pull/") or lowered.startswith("pull/"):
        return "pull"
    if (
        lowered.startswith("refs/heads/")
        or lowered in {"main", "master", "head"}
        or lowered.startswith("origin/")
    ):
        return "branch"
    normalized_commit = normalize_source_commit(normalized)
    if normalized_commit is not None:
        return "commit"
    return "tag"