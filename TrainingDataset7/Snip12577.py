def is_multipart(self):
        """
        Return True if the form needs to be multipart-encoded, i.e. it has
        FileInput, or False otherwise.
        """
        return any(field.widget.needs_multipart_form for field in self.fields.values())