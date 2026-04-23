def test_datetimes_alias(self):
        qs = Store.objects.alias(
            original_opening_alias=F("original_opening"),
        ).datetimes("original_opening_alias", "year")
        self.assertCountEqual(
            qs,
            [
                datetime.datetime(1994, 1, 1),
                datetime.datetime(2001, 1, 1),
            ],
        )