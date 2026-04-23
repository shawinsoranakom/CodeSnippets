def add_index(self, app_label, model_name, index):
        self._append_option(app_label, model_name, "indexes", index)