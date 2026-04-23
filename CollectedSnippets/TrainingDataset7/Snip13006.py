def __init__(self, permitted_methods, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["Allow"] = ", ".join(permitted_methods)