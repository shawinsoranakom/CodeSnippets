def skip_default(self, field):
        default_is_empty = self.effective_default(field) in ("", b"")
        if default_is_empty and self._is_text_or_blob(field):
            return True
        return False