def _get_app_label_and_model_name(model, app_label=""):
    if isinstance(model, str):
        split = model.split(".", 1)
        return tuple(split) if len(split) == 2 else (app_label, split[0])
    else:
        return model._meta.app_label, model._meta.model_name