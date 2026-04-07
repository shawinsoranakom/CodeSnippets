def _allowed_methods(self):
        return [m.upper() for m in self.http_method_names if hasattr(self, m)]