def _prepare_field_lists(self):
        """
        Prepare field lists and a list of the fields that used through models
        in the old state so dependencies can be made from the through model
        deletion to the field that uses it.
        """
        self.kept_model_keys = self.old_model_keys & self.new_model_keys
        self.kept_proxy_keys = self.old_proxy_keys & self.new_proxy_keys
        self.kept_unmanaged_keys = self.old_unmanaged_keys & self.new_unmanaged_keys
        self.through_users = {}
        self.old_field_keys = {
            (app_label, model_name, field_name)
            for app_label, model_name in self.kept_model_keys
            for field_name in self.from_state.models[
                app_label, self.renamed_models.get((app_label, model_name), model_name)
            ].fields
        }
        self.new_field_keys = {
            (app_label, model_name, field_name)
            for app_label, model_name in self.kept_model_keys
            for field_name in self.to_state.models[app_label, model_name].fields
        }