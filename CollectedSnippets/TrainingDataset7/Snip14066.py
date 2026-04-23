def describe(self):
        """
        Format the URL pattern for display in warning messages.
        """
        description = "'{}'".format(self)
        if self.name:
            description += " [name='{}']".format(self.name)
        return description