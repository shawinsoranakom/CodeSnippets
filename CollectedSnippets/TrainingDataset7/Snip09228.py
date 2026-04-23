def _get_database_display_str(self, verbosity, database_name):
        """
        Return display string for a database for use in various actions.
        """
        return "'%s'%s" % (
            self.connection.alias,
            (" ('%s')" % database_name) if verbosity >= 2 else "",
        )