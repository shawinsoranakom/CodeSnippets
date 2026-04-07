def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a model in Auth is involved"
        return obj1._meta.app_label == "auth" or obj2._meta.app_label == "auth" or None