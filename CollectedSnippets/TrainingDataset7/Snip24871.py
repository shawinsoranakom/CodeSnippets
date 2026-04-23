def test_i18n_intcomma(self):
        test_list = (
            100,
            1000,
            10123,
            10311,
            1000000,
            1234567.25,
            "100",
            "1000",
            "10123",
            "10311",
            "1000000",
            None,
        )
        result_list = (
            "100",
            "1.000",
            "10.123",
            "10.311",
            "1.000.000",
            "1.234.567,25",
            "100",
            "1.000",
            "10.123",
            "10.311",
            "1.000.000",
            None,
        )
        with self.settings(USE_THOUSAND_SEPARATOR=True):
            with translation.override("de"):
                self.humanize_tester(test_list, result_list, "intcomma")