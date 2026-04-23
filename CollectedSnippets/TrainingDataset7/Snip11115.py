def _check_decimal_places_and_max_digits(self, **kwargs):
        if self.decimal_places is None or self.max_digits is None:
            return []
        if int(self.decimal_places) > int(self.max_digits):
            return [
                checks.Error(
                    "'max_digits' must be greater or equal to 'decimal_places'.",
                    obj=self,
                    id="fields.E134",
                )
            ]
        return []