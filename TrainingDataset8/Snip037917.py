def __init__(self, cached_value, func_or_code):
        self.cached_value = cached_value
        if inspect.iscode(func_or_code):
            self.cached_func_name = "a code block"
        else:
            self.cached_func_name = _get_cached_func_name_md(func_or_code)