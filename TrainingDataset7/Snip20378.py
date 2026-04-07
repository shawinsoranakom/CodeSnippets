def test_extract_none(self):
        self.create_model(None, None)
        for t in (
            Extract("start_datetime", "year"),
            Extract("start_date", "year"),
            Extract("start_time", "hour"),
        ):
            with self.subTest(t):
                self.assertIsNone(
                    DTModel.objects.annotate(extracted=t).first().extracted
                )