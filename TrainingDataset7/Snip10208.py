def references_model(self, name, app_label):
        """
        Return True if there is a chance this operation references the given
        model name (as a string), with an app label for accuracy.

        Used for optimization. If in doubt, return True;
        returning a false positive will merely make the optimizer a little
        less efficient, while returning a false negative may result in an
        unusable optimized migration.
        """
        return True