def test_method_override(self):
        self.assertEqual(settings.TEST, "override2")
        self.assertEqual(settings.TEST_OUTER, "outer")