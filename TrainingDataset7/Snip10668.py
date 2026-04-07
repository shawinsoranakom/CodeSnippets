def _check_indexes(cls, databases):
        errors = []
        for db in databases:
            if not router.allow_migrate_model(db, cls):
                continue
            connection = connections[db]
            for index in cls._meta.indexes:
                errors.extend(index.check(cls, connection))
        return errors