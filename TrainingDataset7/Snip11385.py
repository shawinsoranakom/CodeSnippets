def _check_relation_model_exists(self):
        rel_is_missing = self.remote_field.model not in self.opts.apps.get_models(
            include_auto_created=True
        )
        rel_is_string = isinstance(self.remote_field.model, str)
        model_name = (
            self.remote_field.model
            if rel_is_string
            else self.remote_field.model._meta.object_name
        )
        if rel_is_missing and (
            rel_is_string or not self.remote_field.model._meta.swapped
        ):
            return [
                checks.Error(
                    "Field defines a relation with model '%s', which is either "
                    "not installed, or is abstract." % model_name,
                    obj=self,
                    id="fields.E300",
                )
            ]
        return []