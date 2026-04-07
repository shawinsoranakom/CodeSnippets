def _require_file(self):
        if not self:
            raise ValueError(
                "The '%s' attribute has no file associated with it." % self.field.name
            )