def y(self):
        """Year, 2 digits with leading zeros; e.g. '99'."""
        return "%02d" % (self.data.year % 100)