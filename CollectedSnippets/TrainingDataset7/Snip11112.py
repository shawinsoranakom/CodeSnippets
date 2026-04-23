def check(self, **kwargs):
        errors = super().check(**kwargs)
        databases = kwargs.get("databases") or []

        digits_errors = [
            *self._check_decimal_places(databases),
            *self._check_max_digits(databases),
        ]
        if not digits_errors:
            errors.extend(self._check_decimal_places_and_max_digits(**kwargs))
        else:
            errors.extend(digits_errors)
        return errors