def _alter_option(self, app_label, model_name, option_name, obj_name, alt_obj):
        model_state = self.models[app_label, model_name]
        objs = model_state.options[option_name]
        model_state.options[option_name] = [
            obj if obj.name != obj_name else alt_obj for obj in objs
        ]
        self.reload_model(app_label, model_name, delay=True)