def find_path_provider[TPathProvider: PathProvider](
    provider_type: t.Type[TPathProvider],
    provider_classes: list[t.Type[TPathProvider]],
    path: str,
    walk: bool,
) -> TPathProvider:
    """Return the first found path provider of the given type for the given path."""
    sequences = sorted(set(pc.sequence for pc in provider_classes if pc.sequence > 0))

    for sequence in sequences:
        candidate_path = path
        tier_classes = [pc for pc in provider_classes if pc.sequence == sequence]

        while True:
            for provider_class in tier_classes:
                if provider_class.is_content_root(candidate_path):
                    return provider_class(candidate_path)

            if not walk:
                break

            parent_path = os.path.dirname(candidate_path)

            if parent_path == candidate_path:
                break

            candidate_path = parent_path

    raise ProviderNotFoundForPath(provider_type, path)