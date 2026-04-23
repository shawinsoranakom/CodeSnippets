def get_view_name(view_func):
    if hasattr(view_func, "view_class"):
        klass = view_func.view_class
        return f"{klass.__module__}.{klass.__qualname__}"
    mod_name = view_func.__module__
    view_name = getattr(view_func, "__qualname__", view_func.__class__.__name__)
    return mod_name + "." + view_name