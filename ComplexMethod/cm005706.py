def get_model_name(obj):
    """
    Get the model name from the file path of the object.
    """

    path = inspect.getsourcefile(obj)
    if path is None:
        return None
    if path.split(os.path.sep)[-3] != "models":
        return None
    file_name = path.split(os.path.sep)[-1]
    model_name_lowercase_from_folder = path.split(os.path.sep)[-2]
    model_name_lowercase_from_file = None
    for file_type in AUTODOC_FILES:
        start = file_type.split("*")[0]
        end = file_type.split("*")[-1] if "*" in file_type else ""
        if file_name.startswith(start) and file_name.endswith(end):
            model_name_lowercase_from_file = file_name[len(start) : -len(end)]
            break
    if model_name_lowercase_from_file and model_name_lowercase_from_folder != model_name_lowercase_from_file:
        from transformers.models.auto.configuration_auto import SPECIAL_MODEL_TYPE_TO_MODULE_NAME

        if (
            model_name_lowercase_from_file in SPECIAL_MODEL_TYPE_TO_MODULE_NAME
            or model_name_lowercase_from_file.replace("_", "-") in SPECIAL_MODEL_TYPE_TO_MODULE_NAME
        ):
            return model_name_lowercase_from_file
        return model_name_lowercase_from_folder
    return model_name_lowercase_from_folder