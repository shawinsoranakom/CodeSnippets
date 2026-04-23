def generate(self):
        day1 = datetime.date(2005, 1, 1)
        Thing.objects.create(
            when="a",
            join="b",
            like="c",
            drop="d",
            alter="e",
            having="f",
            where=day1,
            has_hyphen="h",
        )
        day2 = datetime.date(2006, 2, 2)
        Thing.objects.create(
            when="h",
            join="i",
            like="j",
            drop="k",
            alter="l",
            having="m",
            where=day2,
        )