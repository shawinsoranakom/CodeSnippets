def test_overlaying_app(self):
        # Use a subdirectory so it is outside the PYTHONPATH.
        os.makedirs(os.path.join(self.test_dir, "apps/app1"))
        self.run_django_admin(["startapp", "app1", "apps/app1"])
        out, err = self.run_django_admin(["startapp", "app2", "apps/app1"])
        self.assertOutput(
            err,
            "already exists. Overlaying an app into an existing directory "
            "won't replace conflicting files.",
        )