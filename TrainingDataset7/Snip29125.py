def db_for_read(self, model, instance=None, **hints):
        if instance:
            return instance._state.db or "other"
        return "other"