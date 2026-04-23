def __call__(self, db_field, **kwargs):
        self.log.append((db_field, kwargs))
        return db_field.formfield(**kwargs)