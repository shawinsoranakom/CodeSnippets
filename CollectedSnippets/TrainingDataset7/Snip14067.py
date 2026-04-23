def _check_pattern_startswith_slash(self):
        """
        Check that the pattern does not begin with a forward slash.
        """
        if not settings.APPEND_SLASH:
            # Skip check as it can be useful to start a URL pattern with a
            # slash when APPEND_SLASH=False.
            return []
        if self._regex.startswith(("/", "^/", "^\\/")) and not self._regex.endswith(
            "/"
        ):
            warning = Warning(
                "Your URL pattern {} has a route beginning with a '/'. Remove this "
                "slash as it is unnecessary. If this pattern is targeted in an "
                "include(), ensure the include() pattern has a trailing '/'.".format(
                    self.describe()
                ),
                id="urls.W002",
            )
            return [warning]
        else:
            return []