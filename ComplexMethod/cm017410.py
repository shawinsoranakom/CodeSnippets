def _check_on_delete(self, databases):
        on_delete = getattr(self.remote_field, "on_delete", None)
        errors = []
        if on_delete == DB_CASCADE:
            errors.extend(
                self._check_on_delete_db_support(
                    on_delete, "supports_on_delete_db_cascade", databases
                )
            )
        if on_delete == DB_SET_NULL:
            errors.extend(
                self._check_on_delete_db_support(
                    on_delete, "supports_on_delete_db_null", databases
                )
            )
        if on_delete in [DB_SET_NULL, SET_NULL] and not self.null:
            errors.append(
                checks.Error(
                    f"Field specifies on_delete={on_delete.__name__}, but cannot be "
                    "null.",
                    hint=(
                        "Set null=True argument on the field, or change the on_delete "
                        "rule."
                    ),
                    obj=self,
                    id="fields.E320",
                )
            )
        elif on_delete == SET_DEFAULT and not self.has_default():
            errors.append(
                checks.Error(
                    "Field specifies on_delete=SET_DEFAULT, but has no default value.",
                    hint="Set a default value, or change the on_delete rule.",
                    obj=self,
                    id="fields.E321",
                )
            )
        elif on_delete == DB_SET_DEFAULT:
            if self.db_default is NOT_PROVIDED:
                errors.append(
                    checks.Error(
                        "Field specifies on_delete=DB_SET_DEFAULT, but has "
                        "no db_default value.",
                        hint="Set a db_default value, or change the on_delete rule.",
                        obj=self,
                        id="fields.E322",
                    )
                )
            errors.extend(
                self._check_on_delete_db_support(
                    on_delete, "supports_on_delete_db_default", databases
                )
            )
        if not isinstance(self.remote_field.model, str) and on_delete != DO_NOTHING:
            # Database and Python variants cannot be mixed in a chain of
            # model references.
            is_db_on_delete = isinstance(on_delete, DatabaseOnDelete)
            ref_model_related_fields = (
                ref_model_field.remote_field
                for ref_model_field in self.remote_field.model._meta.get_fields()
                if ref_model_field.related_model
                and hasattr(ref_model_field.remote_field, "on_delete")
            )

            for ref_remote_field in ref_model_related_fields:
                if (
                    ref_remote_field.on_delete is not None
                    and ref_remote_field.on_delete != DO_NOTHING
                    and isinstance(ref_remote_field.on_delete, DatabaseOnDelete)
                    is not is_db_on_delete
                ):
                    on_delete_type = "database" if is_db_on_delete else "Python"
                    ref_on_delete_type = "Python" if is_db_on_delete else "database"
                    errors.append(
                        checks.Error(
                            f"Field specifies {on_delete_type}-level on_delete "
                            "variant, but referenced model uses "
                            f"{ref_on_delete_type}-level variant.",
                            hint=(
                                "Use either database or Python on_delete variants "
                                "uniformly in the references chain."
                            ),
                            obj=self,
                            id="fields.E323",
                        )
                    )
                    break
        return errors