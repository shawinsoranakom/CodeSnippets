def test_signal_callback_context_manager(self):
        with self.assertRaises(AttributeError):
            getattr(settings, "TEST")
        with self.settings(TEST="override"):
            self.assertEqual(self.testvalue, "override")
        self.assertIsNone(self.testvalue)