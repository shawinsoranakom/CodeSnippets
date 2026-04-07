def test_no_warning(self):
        """
        There isn't a warning if there isn't a duplicate destination.
        """
        output = self._collectstatic_output(clear=True)
        self.assertNotIn(self.warning_string, output)