def _check_backend_specific_checks(self, databases=None, **kwargs):
        if databases is None:
            return []
        errors = []
        for alias in databases:
            if router.allow_migrate_model(alias, self.model):
                errors.extend(connections[alias].validation.check_field(self, **kwargs))
        return errors