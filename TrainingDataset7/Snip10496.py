def _remove_option(self, app_label, model_name, option_name, obj_name):
        model_state = self.models[app_label, model_name]
        objs = model_state.options[option_name]
        model_state.options[option_name] = [obj for obj in objs if obj.name != obj_name]
        self.reload_model(app_label, model_name, delay=True)