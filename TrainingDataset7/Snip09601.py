def check(self, **kwargs):
        issues = super().check(**kwargs)
        issues.extend(self._check_sql_mode(**kwargs))
        return issues