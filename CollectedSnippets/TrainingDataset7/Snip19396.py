def test_middleware_installed(self):
        self.assertEqual(base.check_xframe_options_middleware(None), [])