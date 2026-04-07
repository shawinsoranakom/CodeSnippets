def test_apnumber(self):
        test_list = [str(x) for x in range(1, 11)]
        test_list.append(None)
        result_list = (
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "10",
            None,
        )
        with translation.override("en"):
            self.humanize_tester(test_list, result_list, "apnumber")