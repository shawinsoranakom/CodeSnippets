def get_transform(self, lookup_name):
        if lookup_name.startswith("transformfunc_"):
            key, name = lookup_name.split("_", 1)
            return SQLFuncFactory(key, name)
        return super().get_transform(lookup_name)