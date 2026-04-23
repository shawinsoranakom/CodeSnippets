def test_runtime_constructor_sets_instance(self):
        """Creating a Runtime instance sets Runtime.instance"""
        self.assertIsNone(Runtime._instance)
        _ = Runtime(MagicMock())
        self.assertIsNotNone(Runtime._instance)