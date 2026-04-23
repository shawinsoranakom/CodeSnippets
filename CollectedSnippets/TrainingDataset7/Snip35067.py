def test_bad_test_runner(self):
        with self.assertRaises(AttributeError):
            call_command("test", "sites", testrunner="test_runner.NonexistentRunner")