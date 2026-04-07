def callback(db_field, **kwargs):
            callback_args.append((db_field, kwargs))
            return db_field.formfield(**kwargs)