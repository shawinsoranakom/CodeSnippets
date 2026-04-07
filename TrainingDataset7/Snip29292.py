def test_fetch_mode_raise_forward(self):
        r = Restaurant.objects.fetch_mode(RAISE).get(pk=self.r1.pk)
        msg = "Fetching of Restaurant.place blocked."
        with self.assertRaisesMessage(FieldFetchBlocked, msg) as cm:
            r.place
        self.assertIsNone(cm.exception.__cause__)
        self.assertTrue(cm.exception.__suppress_context__)