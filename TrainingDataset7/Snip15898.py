def test_pks_parsing(self):
        """Regression for #20509

        Test would raise an exception rather than printing an error message.
        """
        args = ["dumpdata", "--pks=1"]
        out, err = self.run_manage(args)
        self.assertOutput(err, "You can only use --pks option with one model")
        self.assertNoOutput(out)