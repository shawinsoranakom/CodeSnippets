def test_get_max_test_processes_other(
        self,
        mocked_get_start_method,
        mocked_cpu_count,
    ):
        mocked_get_start_method.return_value = "other"
        self.assertEqual(get_max_test_processes(), 1)
        with mock.patch.dict(os.environ, {"DJANGO_TEST_PROCESSES": "7"}):
            self.assertEqual(get_max_test_processes(), 1)