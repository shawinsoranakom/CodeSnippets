def _get_scheme(self):
        return self.scope.get("scheme") or super()._get_scheme()