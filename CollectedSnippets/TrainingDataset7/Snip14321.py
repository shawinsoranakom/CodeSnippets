def N(self):
        "Month abbreviation in Associated Press style. Proprietary extension."
        return MONTHS_AP[self.data.month]