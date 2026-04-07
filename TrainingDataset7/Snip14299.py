def h(self):
        "Hour, 12-hour format; i.e. '01' to '12'"
        return "%02d" % (self.data.hour % 12 or 12)