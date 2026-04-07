def test_rfc3339_date_with_timezone(self):
        """
        rfc3339_date() correctly formats datetime objects with tzinfo.
        """
        self.assertEqual(
            feedgenerator.rfc3339_date(
                datetime.datetime(
                    2008, 11, 14, 13, 37, 0, tzinfo=get_fixed_timezone(120)
                )
            ),
            "2008-11-14T13:37:00+02:00",
        )