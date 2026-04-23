def test_simple(self):
        day1 = datetime.date(2005, 1, 1)
        t = Thing.objects.create(
            when="a",
            join="b",
            like="c",
            drop="d",
            alter="e",
            having="f",
            where=day1,
            has_hyphen="h",
        )
        self.assertEqual(t.when, "a")

        day2 = datetime.date(2006, 2, 2)
        u = Thing.objects.create(
            when="h",
            join="i",
            like="j",
            drop="k",
            alter="l",
            having="m",
            where=day2,
        )
        self.assertEqual(u.when, "h")