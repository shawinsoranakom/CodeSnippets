def _check_max_digits(self, databases):
        if self.max_digits is None:
            for db in databases:
                if not router.allow_migrate_model(db, self.model):
                    continue
                connection = connections[db]

                if (
                    not connection.features.supports_no_precision_decimalfield
                    and "supports_no_precision_decimalfield"
                    not in self.model._meta.required_db_features
                ):
                    return [
                        checks.Error(
                            "DecimalFields must define a 'max_digits' attribute.",
                            obj=self,
                            id="fields.E132",
                        )
                    ]
                elif self.decimal_places is not None:
                    return [
                        checks.Error(
                            "DecimalField’s max_digits and decimal_places must both "
                            "be defined or both omitted.",
                            obj=self,
                            id="fields.E135",
                        ),
                    ]
        else:
            try:
                max_digits = int(self.max_digits)
                if max_digits <= 0:
                    raise ValueError()
            except ValueError:
                return [
                    checks.Error(
                        "'max_digits' must be a positive integer.",
                        obj=self,
                        id="fields.E133",
                    )
                ]
        return []