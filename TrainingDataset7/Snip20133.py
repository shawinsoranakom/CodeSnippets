def get_lookup(self, lookup_name):
        if lookup_name.startswith("lookupfunc_"):
            key, name = lookup_name.split("_", 1)
            return SQLFuncFactory(key, name)
        return super().get_lookup(lookup_name)