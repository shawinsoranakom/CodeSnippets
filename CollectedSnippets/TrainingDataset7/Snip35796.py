def test_non_regex(self):
        """
        A Resolver404 is raised if resolving doesn't meet the basic
        requirements of a path to match - i.e., at the very least, it matches
        the root pattern '^/'. Never return None from resolve() to prevent a
        TypeError from occurring later (#10834).
        """
        test_urls = ["", "a", "\\", "."]
        for path_ in test_urls:
            with self.subTest(path=path_):
                with self.assertRaises(Resolver404):
                    resolve(path_)