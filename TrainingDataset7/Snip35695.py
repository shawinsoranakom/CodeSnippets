def test_str(self):
        self.assertEqual(str(RoutePattern(_("translated/"))), "translated/")