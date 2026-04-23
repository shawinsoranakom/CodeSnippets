def _check_decimal_places(self, databases):
        if self.decimal_places is None:
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
                            "DecimalFields must define a 'decimal_places' attribute.",
                            obj=self,
                            id="fields.E130",
                        )
                    ]
                elif self.max_digits is not None:
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
                decimal_places = int(self.decimal_places)
                if decimal_places < 0:
                    raise ValueError()
            except ValueError:
                return [
                    checks.Error(
                        "'decimal_places' must be a non-negative integer.",
                        obj=self,
                        id="fields.E131",
                    )
                ]
        return []