def db_for_write(self, model, **hints):
            raise RouterUsed(mode=RouterUsed.WRITE, model=model, hints=hints)