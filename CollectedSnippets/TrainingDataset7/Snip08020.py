def load(self):
        session_data = {}
        try:
            with open(self._key_to_file(), encoding="ascii") as session_file:
                file_data = session_file.read()
            # Don't fail if there is no data in the session file.
            # We may have opened the empty placeholder file.
            if file_data:
                try:
                    session_data = self.decode(file_data)
                except (EOFError, SuspiciousOperation) as e:
                    if isinstance(e, SuspiciousOperation):
                        logger = logging.getLogger(
                            "django.security.%s" % e.__class__.__name__
                        )
                        logger.warning(str(e))
                    self.create()

                # Remove expired sessions.
                expiry_age = self.get_expiry_age(expiry=self._expiry_date(session_data))
                if expiry_age <= 0:
                    session_data = {}
                    self.delete()
                    self.create()
        except (OSError, SuspiciousOperation):
            self._session_key = None
        return session_data