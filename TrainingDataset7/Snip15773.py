def test_broken_app(self):
        """manage.py check reports an ImportError if an app's models.py
        raises one on import"""

        self.write_settings("settings.py", apps=["admin_scripts.broken_app"])
        args = ["check"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "ImportError")