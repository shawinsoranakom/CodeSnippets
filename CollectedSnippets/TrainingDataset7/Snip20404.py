def test_trunc_none(self):
        self.create_model(None, None)
        for t in (
            Trunc("start_datetime", "year"),
            Trunc("start_date", "year"),
            Trunc("start_time", "hour"),
        ):
            with self.subTest(t):
                self.assertIsNone(
                    DTModel.objects.annotate(truncated=t).first().truncated
                )