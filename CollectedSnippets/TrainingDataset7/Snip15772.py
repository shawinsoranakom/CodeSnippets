def test_nonexistent_app(self):
        """check reports an error on a nonexistent app in INSTALLED_APPS."""
        self.write_settings(
            "settings.py",
            apps=["admin_scriptz.broken_app"],
            sdict={"USE_I18N": False},
        )
        args = ["check"]
        out, err = self.run_manage(args)
        self.assertNoOutput(out)
        self.assertOutput(err, "ModuleNotFoundError")
        self.assertOutput(err, "No module named")
        self.assertOutput(err, "admin_scriptz")