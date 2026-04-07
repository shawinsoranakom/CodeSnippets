def test_version(self):
        "version is handled as a special case"
        args = ["version"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        self.assertOutput(out, get_version())