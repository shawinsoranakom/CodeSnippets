def test_labels_valid(self):
        enums = (
            Separator,
            Constants,
            Set,
            MoonLandings,
            DateAndTime,
            MealTimes,
            Frequency,
            Number,
            IPv4Address,
            IPv6Address,
            IPv4Network,
            IPv6Network,
        )
        for choice_enum in enums:
            with self.subTest(choice_enum.__name__):
                self.assertNotIn(None, choice_enum.labels)