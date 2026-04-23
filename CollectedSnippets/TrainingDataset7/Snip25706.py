def test_circular_dependency(self):
        # validate is just an example command to trigger settings configuration
        out, err = self.run_manage(["check"])
        self.assertNoOutput(err)
        self.assertOutput(out, "System check identified no issues (0 silenced).")