def as_text(self, attrs=None, **kwargs):
        """
        Return a string of HTML for representing this as an
        <input type="text">.
        """
        return self.as_widget(TextInput(), attrs, **kwargs)