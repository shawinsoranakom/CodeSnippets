def test_version_alternative(self):
        "--version is equivalent to version"
        args1, args2 = ["version"], ["--version"]
        # It's possible one outputs on stderr and the other on stdout, hence
        # the set
        self.assertEqual(set(self.run_manage(args1)), set(self.run_manage(args2)))