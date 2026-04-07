def lookups(self, request, model_admin):
        if self.value() == "the 80s":
            return (("the 90s", "the 1990's"),)
        elif self.value() == "the 90s":
            return (("the 80s", "the 1980's"),)
        else:
            return (
                ("the 80s", "the 1980's"),
                ("the 90s", "the 1990's"),
            )