def assertSelectOptions(self, selector, values):
        """
        Assert that the <SELECT> widget identified by `selector` has the
        options with the given `values`.
        """
        self._assertOptionsValues("%s > option" % selector, values)