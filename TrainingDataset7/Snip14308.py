def b(self):
        "Month, textual, 3 letters, lowercase; e.g. 'jan'"
        return MONTHS_3[self.data.month]