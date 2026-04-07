def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Handle the simpler arguments.
        if self.db_table is not None:
            kwargs["db_table"] = self.db_table
        if self.remote_field.db_constraint is not True:
            kwargs["db_constraint"] = self.remote_field.db_constraint
        # Lowercase model names as they should be treated as case-insensitive.
        if isinstance(self.remote_field.model, str):
            if "." in self.remote_field.model:
                app_label, model_name = self.remote_field.model.split(".")
                kwargs["to"] = "%s.%s" % (app_label, model_name.lower())
            else:
                kwargs["to"] = self.remote_field.model.lower()
        else:
            kwargs["to"] = self.remote_field.model._meta.label_lower
        if getattr(self.remote_field, "through", None) is not None:
            if isinstance(self.remote_field.through, str):
                kwargs["through"] = self.remote_field.through
            elif not self.remote_field.through._meta.auto_created:
                kwargs["through"] = self.remote_field.through._meta.label
        if through_fields := getattr(self.remote_field, "through_fields", None):
            kwargs["through_fields"] = through_fields
        # If swappable is True, then see if we're actually pointing to the
        # target of a swap.
        swappable_setting = self.swappable_setting
        if swappable_setting is not None:
            # If it's already a settings reference, error.
            if hasattr(kwargs["to"], "setting_name"):
                if kwargs["to"].setting_name != swappable_setting:
                    raise ValueError(
                        "Cannot deconstruct a ManyToManyField pointing to a "
                        "model that is swapped in place of more than one model "
                        "(%s and %s)" % (kwargs["to"].setting_name, swappable_setting)
                    )

            kwargs["to"] = SettingsReference(
                kwargs["to"],
                swappable_setting,
            )
        return name, path, args, kwargs