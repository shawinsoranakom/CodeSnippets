def test_trunc_time_none(self):
        self.create_model(None, None)
        self.assertIsNone(
            DTModel.objects.annotate(truncated=TruncTime("start_datetime"))
            .first()
            .truncated
        )