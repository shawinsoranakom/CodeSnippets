def test_in_select_mismatch(self):
        msg = (
            "The QuerySet value for the 'in' lookup must have 1 "
            "selected fields (received 2)"
        )
        with self.assertRaisesMessage(ValueError, msg):
            Article.objects.filter(id__in=Article.objects.values("id", "headline"))