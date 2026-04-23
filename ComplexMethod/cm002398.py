def get_list_of_repo_model_paths(models_dir):
    # Get list of all models in the library
    models = glob.glob(os.path.join(models_dir, "*/modeling_*.py"))

    # Get list of all deprecated models in the library
    deprecated_models = glob.glob(os.path.join(models_dir, "deprecated", "*"))
    # For each deprecated model, remove the deprecated models from the list of all models as well as the symlink path
    for deprecated_model in deprecated_models:
        deprecated_model_name = "/" + deprecated_model.split("/")[-1] + "/"
        models = [model for model in models if deprecated_model_name not in model]
    # Remove deprecated models
    models = [model for model in models if "/deprecated" not in model]
    # Remove auto
    models = [model for model in models if "/auto/" not in model]
    return models