def test_locale_independent(self):
        """
        Localization of numbers
        """
        with self.settings(USE_THOUSAND_SEPARATOR=False):
            self.assertEqual(
                "66666.66",
                nformat(
                    self.n, decimal_sep=".", decimal_pos=2, grouping=3, thousand_sep=","
                ),
            )
            self.assertEqual(
                "66666A6",
                nformat(
                    self.n, decimal_sep="A", decimal_pos=1, grouping=1, thousand_sep="B"
                ),
            )
            self.assertEqual(
                "66666",
                nformat(
                    self.n, decimal_sep="X", decimal_pos=0, grouping=1, thousand_sep="Y"
                ),
            )

        with self.settings(USE_THOUSAND_SEPARATOR=True):
            self.assertEqual(
                "66,666.66",
                nformat(
                    self.n, decimal_sep=".", decimal_pos=2, grouping=3, thousand_sep=","
                ),
            )
            self.assertEqual(
                "6B6B6B6B6A6",
                nformat(
                    self.n, decimal_sep="A", decimal_pos=1, grouping=1, thousand_sep="B"
                ),
            )
            self.assertEqual(
                "-66666.6", nformat(-66666.666, decimal_sep=".", decimal_pos=1)
            )
            self.assertEqual(
                "-66666.0", nformat(int("-66666"), decimal_sep=".", decimal_pos=1)
            )
            self.assertEqual(
                "10000.0", nformat(self.long, decimal_sep=".", decimal_pos=1)
            )
            self.assertEqual(
                "10,00,00,000.00",
                nformat(
                    100000000.00,
                    decimal_sep=".",
                    decimal_pos=2,
                    grouping=(3, 2, 0),
                    thousand_sep=",",
                ),
            )
            self.assertEqual(
                "1,0,00,000,0000.00",
                nformat(
                    10000000000.00,
                    decimal_sep=".",
                    decimal_pos=2,
                    grouping=(4, 3, 2, 1, 0),
                    thousand_sep=",",
                ),
            )
            self.assertEqual(
                "10000,00,000.00",
                nformat(
                    1000000000.00,
                    decimal_sep=".",
                    decimal_pos=2,
                    grouping=(3, 2, -1),
                    thousand_sep=",",
                ),
            )
            # This unusual grouping/force_grouping combination may be triggered
            # by the intcomma filter.
            self.assertEqual(
                "10000",
                nformat(
                    self.long,
                    decimal_sep=".",
                    decimal_pos=0,
                    grouping=0,
                    force_grouping=True,
                ),
            )
            # date filter
            self.assertEqual(
                "31.12.2009 в 20:50",
                Template('{{ dt|date:"d.m.Y в H:i" }}').render(self.ctxt),
            )
            self.assertEqual(
                "⌚ 10:15", Template('{{ t|time:"⌚ H:i" }}').render(self.ctxt)
            )