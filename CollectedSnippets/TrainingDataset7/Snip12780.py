def value_from_datadict(self, data, files, name):
        "File widgets take data from FILES, not POST"
        getter = files.get
        if self.allow_multiple_selected:
            try:
                getter = files.getlist
            except AttributeError:
                pass
        return getter(name)