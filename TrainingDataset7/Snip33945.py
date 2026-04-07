def test_regroup03(self):
        """
        Regression tests for #17675
        The date template filter has expects_localtime = True
        """
        output = self.engine.render_to_string(
            "regroup03",
            {
                "data": [
                    {"at": date(2012, 2, 14)},
                    {"at": date(2012, 2, 28)},
                    {"at": date(2012, 7, 4)},
                ],
            },
        )
        self.assertEqual(output, "02:1428,07:04,")