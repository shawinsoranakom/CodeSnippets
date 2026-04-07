def test_all_initialized_only(self):
        handler = BaseConnectionHandler({"default": {}})
        self.assertEqual(handler.all(initialized_only=True), [])