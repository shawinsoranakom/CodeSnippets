def test_no_testrunner(self):
        args = ["test", "--testrunner"]
        out, err = self.run_django_admin(args, "test_project.settings")
        self.assertIn("usage", err)
        self.assertNotIn("Traceback", err)
        self.assertNoOutput(out)