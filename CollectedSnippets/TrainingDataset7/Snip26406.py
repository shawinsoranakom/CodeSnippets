def test_fetch_mode_raise_forward(self):
        a = Article.objects.fetch_mode(RAISE).get(pk=self.a.pk)
        msg = "Fetching of Article.reporter blocked."
        with self.assertRaisesMessage(FieldFetchBlocked, msg) as cm:
            a.reporter
        self.assertIsNone(cm.exception.__cause__)
        self.assertTrue(cm.exception.__suppress_context__)