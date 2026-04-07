def test_i18n_html_ordinal(self):
        """Allow html in output on i18n strings"""
        test_list = (
            "1",
            "2",
            "3",
            "4",
            "11",
            "12",
            "13",
            "21",
            "31",
            "101",
            "102",
            "103",
            "111",
            "something else",
            None,
        )
        result_list = (
            "1<sup>er</sup>",
            "2<sup>e</sup>",
            "3<sup>e</sup>",
            "4<sup>e</sup>",
            "11<sup>e</sup>",
            "12<sup>e</sup>",
            "13<sup>e</sup>",
            "21<sup>e</sup>",
            "31<sup>e</sup>",
            "101<sup>e</sup>",
            "102<sup>e</sup>",
            "103<sup>e</sup>",
            "111<sup>e</sup>",
            "something else",
            "None",
        )

        with translation.override("fr-fr"):
            self.humanize_tester(test_list, result_list, "ordinal", lambda x: x)