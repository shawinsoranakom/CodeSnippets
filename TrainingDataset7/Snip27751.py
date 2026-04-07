def test_textchoices(self):
        self.assertEqual(
            YearInSchool.choices,
            [
                ("FR", "Freshman"),
                ("SO", "Sophomore"),
                ("JR", "Junior"),
                ("SR", "Senior"),
                ("GR", "Graduate"),
            ],
        )
        self.assertEqual(
            YearInSchool.labels,
            ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"],
        )
        self.assertEqual(YearInSchool.values, ["FR", "SO", "JR", "SR", "GR"])
        self.assertEqual(
            YearInSchool.names,
            ["FRESHMAN", "SOPHOMORE", "JUNIOR", "SENIOR", "GRADUATE"],
        )

        self.assertEqual(repr(YearInSchool.FRESHMAN), "YearInSchool.FRESHMAN")
        self.assertEqual(YearInSchool.FRESHMAN.label, "Freshman")
        self.assertEqual(YearInSchool.FRESHMAN.value, "FR")
        self.assertEqual(YearInSchool["FRESHMAN"], YearInSchool.FRESHMAN)
        self.assertEqual(YearInSchool("FR"), YearInSchool.FRESHMAN)

        self.assertIsInstance(YearInSchool, type(models.Choices))
        self.assertIsInstance(YearInSchool.FRESHMAN, YearInSchool)
        self.assertIsInstance(YearInSchool.FRESHMAN.label, Promise)
        self.assertIsInstance(YearInSchool.FRESHMAN.value, str)