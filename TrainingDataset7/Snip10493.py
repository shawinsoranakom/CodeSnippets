def remove_model_options(self, app_label, model_name, option_name, value_to_remove):
        model_state = self.models[app_label, model_name]
        if objs := model_state.options.get(option_name):
            new_value = [obj for obj in objs if tuple(obj) != tuple(value_to_remove)]
            if option_name in {"index_together", "unique_together"}:
                new_value = set(normalize_together(new_value))
            model_state.options[option_name] = new_value
        self.reload_model(app_label, model_name, delay=True)