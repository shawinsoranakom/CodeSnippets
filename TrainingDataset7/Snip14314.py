def I(self):  # NOQA: E743, E741
        "'1' if daylight saving time, '0' otherwise."
        if self.timezone is None:
            return ""
        return "1" if self.timezone.dst(self.data) else "0"