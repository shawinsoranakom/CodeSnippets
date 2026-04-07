def test_xframe_deny(self):
        self.assertEqual(base.check_xframe_deny(None), [])