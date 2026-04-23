def S(self):
        """
        English ordinal suffix for the day of the month, 2 characters; i.e.
        'st', 'nd', 'rd' or 'th'.
        """
        if self.data.day in (11, 12, 13):  # Special case
            return "th"
        last = self.data.day % 10
        if last == 1:
            return "st"
        if last == 2:
            return "nd"
        if last == 3:
            return "rd"
        return "th"