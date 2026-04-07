def test_intword(self):
        # Positive integers.
        test_list_positive = (
            "100",
            "1000000",
            "1200000",
            "1290000",
            "1000000000",
            "2000000000",
            "6000000000000",
            "1300000000000000",
            "3500000000000000000000",
            "8100000000000000000000000000000000",
            ("1" + "0" * 100),
            ("1" + "0" * 104),
        )
        result_list_positive = (
            "100",
            "1.0 million",
            "1.2 million",
            "1.3 million",
            "1.0 billion",
            "2.0 billion",
            "6.0 trillion",
            "1.3 quadrillion",
            "3.5 sextillion",
            "8.1 decillion",
            "1.0 googol",
            ("1" + "0" * 104),
        )
        # Negative integers.
        test_list_negative = ("-" + test for test in test_list_positive)
        result_list_negative = ("-" + result for result in result_list_positive)
        with translation.override("en"):
            self.humanize_tester(
                (*test_list_positive, *test_list_negative, None),
                (*result_list_positive, *result_list_negative, None),
                "intword",
            )