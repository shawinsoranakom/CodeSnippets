def test_error_on_timezone(self):
        """Regression test for #8354: the MySQL and Oracle backends should
        raise an error if given a timezone-aware datetime object."""
        dt = datetime.datetime(2008, 8, 31, 16, 20, tzinfo=datetime.UTC)
        d = Donut(name="Bear claw", consumed_at=dt)
        # MySQL backend does not support timezone-aware datetimes.
        with self.assertRaises(ValueError):
            d.save()