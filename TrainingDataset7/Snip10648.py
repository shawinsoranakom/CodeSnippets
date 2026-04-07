def unique_error_message(self, model_class, unique_check):
        opts = model_class._meta

        params = {
            "model": self,
            "model_class": model_class,
            "model_name": capfirst(opts.verbose_name),
            "unique_check": unique_check,
        }

        # A unique field
        if len(unique_check) == 1:
            field = opts.get_field(unique_check[0])
            params["field_label"] = capfirst(field.verbose_name)
            return ValidationError(
                message=field.error_messages["unique"],
                code="unique",
                params=params,
            )

        # unique_together
        else:
            field_labels = [
                capfirst(opts.get_field(f).verbose_name) for f in unique_check
            ]
            params["field_labels"] = get_text_list(field_labels, _("and"))
            return ValidationError(
                message=_("%(model_name)s with this %(field_labels)s already exists."),
                code="unique_together",
                params=params,
            )