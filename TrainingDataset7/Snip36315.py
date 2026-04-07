def test_rfc2822_date_with_timezone(self):
        """
        rfc2822_date() correctly formats datetime objects with tzinfo.
        """
        self.assertEqual(
            feedgenerator.rfc2822_date(
                datetime.datetime(
                    2008, 11, 14, 13, 37, 0, tzinfo=get_fixed_timezone(60)
                )
            ),
            "Fri, 14 Nov 2008 13:37:00 +0100",
        )