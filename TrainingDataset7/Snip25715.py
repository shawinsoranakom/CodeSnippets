def test_custom_logging(self):
        out, err = self.run_manage(["check"])
        self.assertNoOutput(err)
        self.assertOutput(out, "System check identified no issues (0 silenced).")