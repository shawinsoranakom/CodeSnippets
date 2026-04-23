def keep_lazy_text(func):
    """
    A decorator for functions that accept lazy arguments and return text.
    """
    return keep_lazy(str)(func)