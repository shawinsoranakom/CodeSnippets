def check(self, **kwargs):
        errors = super().check(**kwargs)
        databases = kwargs.get("databases") or []
        errors.extend(self._check_supported(databases))
        return errors