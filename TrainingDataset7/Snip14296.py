def f(self):
        """
        Time, in 12-hour hours and minutes, with minutes left off if they're
        zero.
        Examples: '1', '1:30', '2:05', '2'
        Proprietary extension.
        """
        hour = self.data.hour % 12 or 12
        minute = self.data.minute
        return "%d:%02d" % (hour, minute) if minute else hour