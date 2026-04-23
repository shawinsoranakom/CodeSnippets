def normalized_ref_aliases(ref: str | None) -> set[str]:
    if not isinstance(ref, str):
        return set()
    normalized = ref.strip()
    if not normalized:
        return set()
    aliases = {normalized}
    lowered = normalized.lower()
    commit = normalize_source_commit(normalized)
    if commit is not None:
        aliases.add(commit)
    if lowered.startswith("refs/heads/"):
        aliases.add(normalized.split("/", 2)[2])
    elif "/" not in normalized and infer_source_ref_kind(normalized) == "branch":
        aliases.add(f"refs/heads/{normalized}")
    if lowered.startswith("refs/pull/"):
        aliases.add(normalized.removeprefix("refs/"))
    elif lowered.startswith("pull/"):
        aliases.add(f"refs/{normalized}")
    return aliases