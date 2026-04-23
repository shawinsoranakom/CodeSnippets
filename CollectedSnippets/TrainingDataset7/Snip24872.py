def test_i18n_intword(self):
        # Positive integers.
        test_list_positive = (
            "100",
            "1000000",
            "1200000",
            "1290000",
            "1000000000",
            "2000000000",
            "6000000000000",
        )
        result_list_positive = (
            "100",
            "1,0 Million",
            "1,2 Millionen",
            "1,3 Millionen",
            "1,0 Milliarde",
            "2,0 Milliarden",
            "6,0 Billionen",
        )
        # Negative integers.
        test_list_negative = ("-" + test for test in test_list_positive)
        result_list_negative = ("-" + result for result in result_list_positive)
        with self.settings(USE_THOUSAND_SEPARATOR=True):
            with translation.override("de"):
                self.humanize_tester(
                    (*test_list_positive, *test_list_negative),
                    (*result_list_positive, *result_list_negative),
                    "intword",
                )