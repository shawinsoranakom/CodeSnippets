def _check_constraints(cls, databases):
        errors = []
        for db in databases:
            if not router.allow_migrate_model(db, cls):
                continue
            connection = connections[db]
            for constraint in cls._meta.constraints:
                errors.extend(constraint.check(cls, connection))
        return errors