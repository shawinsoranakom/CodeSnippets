def fetch_hf_dataset_card(
    dataset_name: str, hf_token: Optional[str] = None
) -> tuple[Optional[str], Optional[dict]]:
    """
    Fetch HF dataset card (README) and metadata.

    Returns:
        (readme_text, metadata_dict) or (None, None) on failure.
    """
    try:
        from huggingface_hub import DatasetCard

        card = DatasetCard.load(dataset_name, token = hf_token)
        readme = card.text or ""

        # Truncate at sentence boundary
        if len(readme) > README_MAX_CHARS:
            cut = readme[:README_MAX_CHARS].rfind(".")
            if cut > README_MAX_CHARS // 2:
                readme = readme[: cut + 1] + "\n[...truncated]"
            else:
                readme = readme[:README_MAX_CHARS] + "\n[...truncated]"

        # Extract metadata from YAML frontmatter
        metadata = {}
        if card.data:
            for key in (
                "task_categories",
                "task_ids",
                "language",
                "size_categories",
                "tags",
                "license",
                "pretty_name",
            ):
                val = getattr(card.data, key, None)
                if val is not None:
                    metadata[key] = val

        logger.info(
            f"Fetched dataset card: {len(readme)} chars, {len(metadata)} metadata fields"
        )
        return readme, metadata

    except Exception as e:
        logger.warning(f"Could not fetch dataset card for {dataset_name}: {e}")
        return None, None