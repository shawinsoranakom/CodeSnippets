def as_hidden(self, attrs=None, **kwargs):
        """
        Return a string of HTML for representing this as an
        <input type="hidden">.
        """
        return self.as_widget(self.field.hidden_widget(), attrs, **kwargs)