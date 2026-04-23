def as_textarea(self, attrs=None, **kwargs):
        """Return a string of HTML for representing this as a <textarea>."""
        return self.as_widget(Textarea(), attrs, **kwargs)