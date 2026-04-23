def ensure_all_models_in_toctree(model_doc: list[dict]):
    """Make sure that all models in `model_doc` folder are also part of the `_toctree.yml`. Raise if it's not
    the case."""
    all_documented_models = {model_doc_file.removesuffix(".md") for model_doc_file in os.listdir(DOC_PATH)} - {"auto"}
    all_models_in_toctree = {
        model_entry["local"].removeprefix("model_doc/") for section in model_doc for model_entry in section["sections"]
    }

    # everything alright
    if all_documented_models == all_models_in_toctree:
        return

    documented_but_not_in_toctree = all_documented_models - all_models_in_toctree
    in_toctree_but_not_documented = all_models_in_toctree - all_documented_models

    error_msg = ""
    if len(documented_but_not_in_toctree) > 0:
        error_msg += (
            f"{documented_but_not_in_toctree} appear(s) inside the folder `model_doc`, but not in the `_toctree.yml`. "
            "Please add it/them in their corresponding section inside the `_toctree.yml`."
        )
    if len(in_toctree_but_not_documented) > 0:
        if len(error_msg) > 0:
            error_msg += "\n"
        error_msg += (
            f"{in_toctree_but_not_documented} appear(s) in the `_toctree.yml`, but not inside the folder `model_doc`. "
            "Please add a corresponding `model.md` in `model_doc`."
        )

    raise ValueError(error_msg)