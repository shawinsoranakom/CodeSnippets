def check(self, *args, **kwargs):
        errors = super().check(*args, **kwargs)
        errors.extend(self._check_postgres_installed(*args))
        return errors