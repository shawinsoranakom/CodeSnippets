def _check_max_length_attribute(self, **kwargs):
        if self.max_length is None:
            if (
                connection.features.supports_unlimited_charfield
                or "supports_unlimited_charfield"
                in self.model._meta.required_db_features
            ):
                return []
            return [
                checks.Error(
                    "CharFields must define a 'max_length' attribute.",
                    obj=self,
                    id="fields.E120",
                )
            ]
        elif (
            not isinstance(self.max_length, int)
            or isinstance(self.max_length, bool)
            or self.max_length <= 0
        ):
            return [
                checks.Error(
                    "'max_length' must be a positive integer.",
                    obj=self,
                    id="fields.E121",
                )
            ]
        else:
            return []