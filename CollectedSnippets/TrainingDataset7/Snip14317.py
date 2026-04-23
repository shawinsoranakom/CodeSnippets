def L(self):
        "Boolean for whether it is a leap year; i.e. True or False"
        return calendar.isleap(self.data.year)