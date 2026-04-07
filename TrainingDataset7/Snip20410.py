def test_trunc_date_none(self):
        self.create_model(None, None)
        self.assertIsNone(
            DTModel.objects.annotate(truncated=TruncDate("start_datetime"))
            .first()
            .truncated
        )