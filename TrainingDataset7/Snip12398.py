def _make_id(target):
    if hasattr(target, "__func__"):
        return (id(target.__self__), id(target.__func__))
    return id(target)