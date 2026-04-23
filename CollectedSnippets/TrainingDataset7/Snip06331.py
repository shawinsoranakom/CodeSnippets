def set_password(self, raw_password):
        raise NotImplementedError(
            "Django doesn't provide a DB representation for AnonymousUser."
        )