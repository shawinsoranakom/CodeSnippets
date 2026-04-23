def d(self):
        "Day of the month, 2 digits with leading zeros; i.e. '01' to '31'"
        return "%02d" % self.data.day