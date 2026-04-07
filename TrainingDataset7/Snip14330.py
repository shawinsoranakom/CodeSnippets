def Y(self):
        """Year, 4 digits with leading zeros; e.g. '1999'."""
        return "%04d" % self.data.year