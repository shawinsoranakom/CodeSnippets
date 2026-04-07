def is_secure(self):
        return getattr(self, "_is_secure_override", False)