def test_lazy_in_settings(self):
        out, err = self.run_manage(["check"])
        self.assertNoOutput(err)