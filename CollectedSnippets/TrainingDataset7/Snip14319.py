def M(self):
        "Month, textual, 3 letters; e.g. 'Jan'"
        return MONTHS_3[self.data.month].title()