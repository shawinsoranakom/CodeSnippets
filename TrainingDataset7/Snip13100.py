def module_path(self):
        return f"{self.func.__module__}.{self.func.__qualname__}"