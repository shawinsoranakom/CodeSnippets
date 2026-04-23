def D(self):
        "Day of the week, textual, 3 letters; e.g. 'Fri'"
        return WEEKDAYS_ABBR[self.data.weekday()]