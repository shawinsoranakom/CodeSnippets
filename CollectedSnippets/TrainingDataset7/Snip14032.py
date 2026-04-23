def decorator(obj):
        if hasattr(obj, "tags"):
            obj.tags = obj.tags.union(tags)
        else:
            setattr(obj, "tags", set(tags))
        return obj