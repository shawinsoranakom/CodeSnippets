def signal_callback(self, sender, setting, value, **kwargs):
        if setting == "TEST":
            self.testvalue = value