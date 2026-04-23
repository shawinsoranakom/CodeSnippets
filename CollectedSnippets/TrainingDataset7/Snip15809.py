def test_help_short_altert(self):
        "-h is handled as a short form of --help"
        args1, args2 = ["--help"], ["-h"]
        self.assertEqual(self.run_manage(args1), self.run_manage(args2))