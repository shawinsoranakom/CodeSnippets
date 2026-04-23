def tag(*tags):
    """Decorator to add tags to a test class or method."""

    def decorator(obj):
        if hasattr(obj, "tags"):
            obj.tags = obj.tags.union(tags)
        else:
            setattr(obj, "tags", set(tags))
        return obj

    return decorator