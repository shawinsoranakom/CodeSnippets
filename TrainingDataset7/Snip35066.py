def test_custom_test_runner(self):
        call_command("test", "sites", testrunner="test_runner.tests.MockTestRunner")
        MockTestRunner.run_tests.assert_called_with(("sites",))