def _post_clean(self):
        super()._post_clean()
        if self.instance is not None and self.instance.position == 1:
            self.add_error(None, ValidationError("A non-field error"))