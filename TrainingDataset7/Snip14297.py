def g(self):
        "Hour, 12-hour format without leading zeros; i.e. '1' to '12'"
        return self.data.hour % 12 or 12