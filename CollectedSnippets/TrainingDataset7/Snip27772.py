def default(self, o):
        if isinstance(o, models.JSONNull):
            return None
        return super().default(o)