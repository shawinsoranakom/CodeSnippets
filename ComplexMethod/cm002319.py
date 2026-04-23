def check_model_type_doc_match():
    """Check all doc pages have a corresponding model type."""
    model_doc_folder = Path(PATH_TO_DOC) / "model_doc"
    model_docs = [m.stem for m in model_doc_folder.glob("*.md")]

    model_types = list(transformers.models.auto.configuration_auto.CONFIG_MAPPING_NAMES.keys())
    model_types += list(DOC_MODEL_NAMES_NOT_IN_AUTO)
    model_types = [MODEL_TYPE_TO_DOC_MAPPING.get(m, m) for m in model_types]

    errors = []
    for m in model_docs:
        if m not in model_types and m != "auto":
            close_matches = get_close_matches(m, model_types)
            error_message = f"{m} is not a proper model identifier."
            if len(close_matches) > 0:
                close_matches = "/".join(close_matches)
                error_message += f" Did you mean {close_matches}?"
            errors.append(error_message)

    if len(errors) > 0:
        raise ValueError(
            "Some model doc pages do not match any existing model type:\n"
            + "\n".join(errors)
            + "\nYou can add any missing model type to the `DOC_MODEL_NAMES_NOT_IN_AUTO` constant in "
            "utils/check_repo.py."
        )