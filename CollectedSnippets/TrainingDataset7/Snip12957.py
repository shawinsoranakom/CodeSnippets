def _content_type_for_repr(self):
        return (
            ', "%s"' % self.headers["Content-Type"]
            if "Content-Type" in self.headers
            else ""
        )