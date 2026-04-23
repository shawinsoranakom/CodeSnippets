def check_model_doc(overwrite: bool = False):
    """
    Check that the content of the table of content in `_toctree.yml` is up-to-date (i.e. it contains all models) and
    clean (no duplicates and sorted for the model API doc) and potentially auto-cleans it.

    Args:
        overwrite (`bool`, *optional*, defaults to `False`):
            Whether to just check if the TOC is clean or to auto-clean it (when `overwrite=True`).
    """
    with open(TOCTREE_PATH, encoding="utf-8") as f:
        content = yaml.safe_load(f.read())

    # Get to the API doc
    api_idx = 0
    while content[api_idx]["title"] != "API":
        api_idx += 1
    api_doc = content[api_idx]["sections"]

    # Then to the model doc
    model_idx = 0
    while api_doc[model_idx]["title"] != "Models":
        model_idx += 1

    model_doc = api_doc[model_idx]["sections"]

    # Make sure the toctree contains all models
    ensure_all_models_in_toctree(model_doc)

    # Extract the modalities and clean them one by one.
    modalities_docs = [(idx, section) for idx, section in enumerate(model_doc) if "sections" in section]
    diff = False
    for idx, modality_doc in modalities_docs:
        old_modality_doc = modality_doc["sections"]
        new_modality_doc = clean_model_doc_toc(old_modality_doc)

        if old_modality_doc != new_modality_doc:
            diff = True
            if overwrite:
                model_doc[idx]["sections"] = new_modality_doc

    if diff:
        if overwrite:
            api_doc[model_idx]["sections"] = model_doc
            content[api_idx]["sections"] = api_doc
            with open(TOCTREE_PATH, "w", encoding="utf-8") as f:
                f.write(yaml.dump(content, allow_unicode=True))
        else:
            raise ValueError(
                "The model doc part of the table of content is not properly sorted, run `make fix-repo` to fix this."
            )