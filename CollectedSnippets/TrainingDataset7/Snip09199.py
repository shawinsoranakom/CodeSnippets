def close_if_unusable_or_obsolete(self):
        """
        Close the current connection if unrecoverable errors have occurred
        or if it outlived its maximum age.
        """
        if self.connection is not None:
            self.health_check_done = False
            # If the application didn't restore the original autocommit
            # setting, don't take chances, drop the connection.
            if self.get_autocommit() != self.settings_dict["AUTOCOMMIT"]:
                self.close()
                return

            # If an exception other than DataError or IntegrityError occurred
            # since the last commit / rollback, check if the connection works.
            if self.errors_occurred:
                if self.is_usable():
                    self.errors_occurred = False
                    self.health_check_done = True
                else:
                    self.close()
                    return

            if self.close_at is not None and time.monotonic() >= self.close_at:
                self.close()
                return