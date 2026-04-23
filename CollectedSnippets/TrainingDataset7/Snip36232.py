def test_e_format_with_time_zone_with_unimplemented_tzname(self):
        class NoNameTZ(tzinfo):
            """Time zone without .tzname() defined."""

            def utcoffset(self, dt):
                return None

        dt = datetime(1970, 1, 1, tzinfo=NoNameTZ())
        self.assertEqual(dateformat.format(dt, "e"), "")