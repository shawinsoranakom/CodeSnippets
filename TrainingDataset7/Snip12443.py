def is_hidden(self):
        """Return True if this BoundField's widget is hidden."""
        return self.field.widget.is_hidden