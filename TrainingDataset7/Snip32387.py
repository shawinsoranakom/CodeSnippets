def test_base_finder_check_not_implemented(self):
        finder = BaseFinder()
        msg = (
            "subclasses may provide a check() method to verify the finder is "
            "configured correctly."
        )
        with self.assertRaisesMessage(NotImplementedError, msg):
            finder.check()