def _load_field(app_label, model_name, field_name):
    return apps.get_model(app_label, model_name)._meta.get_field(field_name)