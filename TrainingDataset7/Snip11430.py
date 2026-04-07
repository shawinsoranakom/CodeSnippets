def check(self, **kwargs):
        databases = kwargs.get("databases") or []
        return [
            *super().check(**kwargs),
            *self._check_on_delete(databases),
            *self._check_unique(),
        ]