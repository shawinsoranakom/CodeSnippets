def clean_model_doc_toc(model_doc: list[dict]) -> list[dict]:
    """
    Cleans a section of the table of content of the model documentation (one specific modality) by removing duplicates
    and sorting models alphabetically.

    Args:
        model_doc (`List[dict]`):
            The list of dictionaries extracted from the `_toctree.yml` file for this specific modality.

    Returns:
        `List[dict]`: List of dictionaries like the input, but cleaned up and sorted.
    """
    counts = defaultdict(int)
    for doc in model_doc:
        counts[doc["local"]] += 1
    duplicates = [key for key, value in counts.items() if value > 1]

    new_doc = []
    for duplicate_key in duplicates:
        titles = list({doc["title"] for doc in model_doc if doc["local"] == duplicate_key})
        if len(titles) > 1:
            raise ValueError(
                f"{duplicate_key} is present several times in the documentation table of content at "
                "`docs/source/en/_toctree.yml` with different *Title* values. Choose one of those and remove the "
                "others."
            )
        # Only add this once
        new_doc.append({"local": duplicate_key, "title": titles[0]})

    # Add none duplicate-keys
    new_doc.extend([doc for doc in model_doc if counts[doc["local"]] == 1])

    # Sort
    return sorted(new_doc, key=lambda s: s["title"].lower())