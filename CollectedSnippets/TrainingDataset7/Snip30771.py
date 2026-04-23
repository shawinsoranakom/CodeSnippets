def test_invalid_index(self):
        msg = "QuerySet indices must be integers or slices, not str."
        with self.assertRaisesMessage(TypeError, msg):
            Article.objects.all()["foo"]