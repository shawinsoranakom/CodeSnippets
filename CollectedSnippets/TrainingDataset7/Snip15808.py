def test_help_alternative(self):
        "--help is equivalent to help"
        args1, args2 = ["help"], ["--help"]
        self.assertEqual(self.run_manage(args1), self.run_manage(args2))