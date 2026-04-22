def is_expired(self) -> bool:
        """Returns true if expiration_date is in the past."""
        if not self.deprecated:
            return False

        expiration_date = _parse_yyyymmdd_str(self.expiration_date)
        now = datetime.datetime.now()
        return now > expiration_date