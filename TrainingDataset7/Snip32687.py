def test_check(self):
        errors = list(default_task_backend.check())
        self.assertEqual(len(errors), 0, errors)