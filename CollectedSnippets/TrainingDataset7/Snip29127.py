def allow_relation(self, obj1, obj2, **hints):
        return obj1._state.db in ("default", "other") and obj2._state.db in (
            "default",
            "other",
        )