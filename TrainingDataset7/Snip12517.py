def choices(self, value):
        # Setting choices on the field also sets the choices on the widget.
        # Note that the property setter for the widget will re-normalize.
        self._choices = self.widget.choices = normalize_choices(value)