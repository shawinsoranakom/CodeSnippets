def approved_hash_for_attempt(attempt: AssetChoice) -> ApprovedArtifactHash | None:
        candidate_names = [attempt.name]
        if (
            isinstance(attempt.tag, str)
            and attempt.tag
            and attempt.tag != checksums.upstream_tag
            and attempt.name.startswith("llama-")
        ):
            legacy_prefix = f"llama-{attempt.tag}-"
            compatibility_prefix = f"llama-{checksums.upstream_tag}-"
            compatibility_name = (
                attempt.name.replace(legacy_prefix, compatibility_prefix, 1)
                if attempt.name.startswith(legacy_prefix)
                else attempt.name
            )
            candidate_names.append(compatibility_name)
        candidate_names.extend(
            windows_cuda_asset_aliases(
                attempt.name,
                compatibility_tag = checksums.upstream_tag,
            )
        )
        seen_names: set[str] = set()
        for candidate_name in candidate_names:
            if candidate_name in seen_names:
                continue
            seen_names.add(candidate_name)
            approved = checksums.artifacts.get(candidate_name)
            if approved is not None:
                return approved
        return None