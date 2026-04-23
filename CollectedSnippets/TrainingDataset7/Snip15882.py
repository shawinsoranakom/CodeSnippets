def test_importable_target_name(self):
        _, err = self.run_django_admin(["startapp", "app", "os"])
        self.assertOutput(
            err,
            "CommandError: 'os' conflicts with the name of an existing Python "
            "module and cannot be used as an app directory. Please try "
            "another directory.",
        )