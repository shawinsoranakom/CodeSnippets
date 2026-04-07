def db_for_write(self, model, **hints):
        if not hasattr(model, "_meta"):
            raise ValueError