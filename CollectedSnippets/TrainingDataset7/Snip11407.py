def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["on_delete"] = self.remote_field.on_delete
        kwargs["from_fields"] = self.from_fields
        kwargs["to_fields"] = self.to_fields

        if self.remote_field.parent_link:
            kwargs["parent_link"] = self.remote_field.parent_link
        if isinstance(self.remote_field.model, str):
            if "." in self.remote_field.model:
                app_label, model_name = self.remote_field.model.split(".")
                kwargs["to"] = "%s.%s" % (app_label, model_name.lower())
            else:
                kwargs["to"] = self.remote_field.model.lower()
        else:
            kwargs["to"] = self.remote_field.model._meta.label_lower
        # If swappable is True, then see if we're actually pointing to the
        # target of a swap.
        swappable_setting = self.swappable_setting
        if swappable_setting is not None:
            # If it's already a settings reference, error
            if hasattr(kwargs["to"], "setting_name"):
                if kwargs["to"].setting_name != swappable_setting:
                    raise ValueError(
                        "Cannot deconstruct a ForeignKey pointing to a model "
                        "that is swapped in place of more than one model (%s and %s)"
                        % (kwargs["to"].setting_name, swappable_setting)
                    )
            # Set it
            kwargs["to"] = SettingsReference(
                kwargs["to"],
                swappable_setting,
            )
        return name, path, args, kwargs