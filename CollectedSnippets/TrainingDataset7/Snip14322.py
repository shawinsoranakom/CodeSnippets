def o(self):
        "ISO 8601 year number matching the ISO week number (W)"
        return self.data.isocalendar().year