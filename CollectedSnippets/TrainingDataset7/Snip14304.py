def s(self):
        "Seconds; i.e. '00' to '59'"
        return "%02d" % self.data.second