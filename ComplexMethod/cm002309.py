def check_model_list():
    """
    Checks the model listed as subfolders of `models` match the models available in `transformers.models`.
    """
    # Get the models from the directory structure of `src/transformers/models/`
    import transformers as tfrs

    models_dir = os.path.join(PATH_TO_TRANSFORMERS, "models")
    _models = []
    for model in os.listdir(models_dir):
        if model == "deprecated":
            continue
        model_dir = os.path.join(models_dir, model)
        if os.path.isdir(model_dir) and "__init__.py" in os.listdir(model_dir):
            # If the init is empty, and there are only two files, it's likely that there's just a conversion
            # script. Those should not be in the init.
            if (Path(model_dir) / "__init__.py").read_text().strip() == "":
                continue

            _models.append(model)

    # Get the models in the submodule `transformers.models`
    models = [model for model in dir(tfrs.models) if not model.startswith("__")]

    missing_models = sorted(set(_models).difference(models))
    if missing_models:
        raise Exception(
            f"The following models should be included in {models_dir}/__init__.py: {','.join(missing_models)}."
        )