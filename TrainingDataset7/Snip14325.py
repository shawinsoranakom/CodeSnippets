def t(self):
        "Number of days in the given month; i.e. '28' to '31'"
        return calendar.monthrange(self.data.year, self.data.month)[1]