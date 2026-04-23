def _find_reload_model(self, app_label, model_name, delay=False):
        if delay:
            self.is_delayed = True

        related_models = set()

        try:
            old_model = self.apps.get_model(app_label, model_name)
        except LookupError:
            pass
        else:
            # Get all relations to and from the old model before reloading,
            # as _meta.apps may change
            if delay:
                related_models = get_related_models_tuples(old_model)
            else:
                related_models = get_related_models_recursive(old_model)

        # Get all outgoing references from the model to be rendered
        model_state = self.models[(app_label, model_name)]
        # Directly related models are the models pointed to by ForeignKeys,
        # OneToOneFields, and ManyToManyFields.
        direct_related_models = set()
        for field in model_state.fields.values():
            if field.is_relation:
                if field.remote_field.model == RECURSIVE_RELATIONSHIP_CONSTANT:
                    continue
                rel_app_label, rel_model_name = _get_app_label_and_model_name(
                    field.related_model, app_label
                )
                direct_related_models.add((rel_app_label, rel_model_name.lower()))

        # For all direct related models recursively get all related models.
        related_models.update(direct_related_models)
        for rel_app_label, rel_model_name in direct_related_models:
            try:
                rel_model = self.apps.get_model(rel_app_label, rel_model_name)
            except LookupError:
                pass
            else:
                if delay:
                    related_models.update(get_related_models_tuples(rel_model))
                else:
                    related_models.update(get_related_models_recursive(rel_model))

        # Include the model itself
        related_models.add((app_label, model_name))

        return related_models