def get_check_kwargs(self, options):
        """Validation is called explicitly each time the server reloads."""
        return {"tags": set()}