def test_defer_fetch_mode_raise(self):
        p1 = Primary.objects.fetch_mode(RAISE).defer("value").get(name="p1")
        msg = "Fetching of Primary.value blocked."
        with self.assertRaisesMessage(FieldFetchBlocked, msg) as cm:
            p1.value
        self.assertIsNone(cm.exception.__cause__)
        self.assertTrue(cm.exception.__suppress_context__)