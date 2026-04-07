def assert_no_memory_leaks(self):
        garbage_collect()
        self.assertEqual(gc.garbage, [])