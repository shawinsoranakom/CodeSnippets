def get_class_lookups(cls):
        bases = inspect.getmro(cls)
        bases = bases[: bases.index(ForeignObject) + 1]
        class_lookups = [parent.__dict__.get("class_lookups", {}) for parent in bases]
        return cls.merge_dicts(class_lookups)