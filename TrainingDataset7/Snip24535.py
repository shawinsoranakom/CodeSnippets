def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)