def test_get_max_test_processes(self, *mocked_objects):
        self.assertEqual(get_max_test_processes(), 12)