def _widget_data_value(self, widget, html_name):
        # value_from_datadict() gets the data from the data dictionaries.
        # Each widget type knows how to retrieve its own data, because some
        # widgets split data over several HTML fields.
        return widget.value_from_datadict(self.data, self.files, html_name)