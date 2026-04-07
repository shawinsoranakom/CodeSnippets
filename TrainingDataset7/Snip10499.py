def remove_index(self, app_label, model_name, index_name):
        self._remove_option(app_label, model_name, "indexes", index_name)