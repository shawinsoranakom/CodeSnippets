def test_system_checks(self):
        self.assertEqual(models.Person.system_check_run_count, 1)