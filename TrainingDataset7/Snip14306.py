def u(self):
        "Microseconds; i.e. '000000' to '999999'"
        return "%06d" % self.data.microsecond