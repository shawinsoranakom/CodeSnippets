def alter_model_managers(self, app_label, model_name, managers):
        model_state = self.models[app_label, model_name]
        model_state.managers = list(managers)
        self.reload_model(app_label, model_name, delay=True)