def _check_pattern_name(self):
        """
        Check that the pattern name does not contain a colon.
        """
        if self.pattern.name is not None and ":" in self.pattern.name:
            warning = Warning(
                "Your URL pattern {} has a name including a ':'. Remove the colon, to "
                "avoid ambiguous namespace references.".format(self.pattern.describe()),
                id="urls.W003",
            )
            return [warning]
        else:
            return []