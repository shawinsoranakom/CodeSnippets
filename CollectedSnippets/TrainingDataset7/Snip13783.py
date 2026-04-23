def run_checks(self, databases):
        # Checks are run after database creation since some checks require
        # database access.
        call_command("check", verbosity=self.verbosity, databases=databases)