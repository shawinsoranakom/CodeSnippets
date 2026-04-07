def _check_referencing_to_swapped_model(self):
        if (
            self.remote_field.model not in self.opts.apps.get_models()
            and not isinstance(self.remote_field.model, str)
            and self.remote_field.model._meta.swapped
        ):
            return [
                checks.Error(
                    "Field defines a relation with the model '%s', which has "
                    "been swapped out." % self.remote_field.model._meta.label,
                    hint="Update the relation to point at 'settings.%s'."
                    % self.remote_field.model._meta.swappable,
                    obj=self,
                    id="fields.E301",
                )
            ]
        return []