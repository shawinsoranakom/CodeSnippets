def test_repercent_broken_unicode_recursion_error(self):
        # Prepare a string long enough to force a recursion error if the tested
        # function uses recursion.
        data = b"\xfc" * sys.getrecursionlimit()
        try:
            self.assertEqual(
                repercent_broken_unicode(data), b"%FC" * sys.getrecursionlimit()
            )
        except RecursionError:
            self.fail("Unexpected RecursionError raised.")