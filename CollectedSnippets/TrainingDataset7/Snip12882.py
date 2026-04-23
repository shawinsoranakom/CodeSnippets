def _set_content_type_params(self, meta):
        """Set content_type, content_params, and encoding."""
        self.content_type, self.content_params = parse_header_parameters(
            meta.get("CONTENT_TYPE", "")
        )
        if "charset" in self.content_params:
            try:
                codecs.lookup(self.content_params["charset"])
            except LookupError:
                pass
            else:
                self.encoding = self.content_params["charset"]