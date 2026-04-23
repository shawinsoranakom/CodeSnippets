def needs_multipart_form(self):
        return any(w.needs_multipart_form for w in self.widgets)