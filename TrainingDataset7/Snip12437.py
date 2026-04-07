def data(self):
        """
        Return the data for this BoundField, or None if it wasn't given.
        """
        return self.form._widget_data_value(self.field.widget, self.html_name)