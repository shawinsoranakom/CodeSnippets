def H(self):
        "Hour, 24-hour format; i.e. '00' to '23'"
        return "%02d" % self.data.hour