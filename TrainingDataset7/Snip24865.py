def test_ordinal(self):
        test_list = (
            "1",
            "2",
            "3",
            "4",
            "11",
            "12",
            "13",
            "101",
            "102",
            "103",
            "111",
            "-0",
            "-1",
            "-105",
            "something else",
            None,
        )
        result_list = (
            "1st",
            "2nd",
            "3rd",
            "4th",
            "11th",
            "12th",
            "13th",
            "101st",
            "102nd",
            "103rd",
            "111th",
            "0th",
            "-1",
            "-105",
            "something else",
            None,
        )

        with translation.override("en"):
            self.humanize_tester(test_list, result_list, "ordinal")