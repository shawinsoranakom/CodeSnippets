def test_get_max_test_processes_env_var(self, *mocked_objects):
        self.assertEqual(get_max_test_processes(), 7)