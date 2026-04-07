def test_fetch_mode_raise_reverse(self):
        p = Place.objects.fetch_mode(RAISE).get(pk=self.p1.pk)
        msg = "Fetching of Place.restaurant blocked."
        with self.assertRaisesMessage(FieldFetchBlocked, msg) as cm:
            p.restaurant
        self.assertIsNone(cm.exception.__cause__)
        self.assertTrue(cm.exception.__suppress_context__)