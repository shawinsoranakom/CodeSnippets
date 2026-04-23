def serialize(self):
        path = self.value.__class__.__module__
        return f"{path}.{self.value.__name__}", {f"import {path}"}