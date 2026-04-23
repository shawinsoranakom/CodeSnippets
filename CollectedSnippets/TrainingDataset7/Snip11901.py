def db_returning_fields(self):
        """
        Private API intended only to be used by Django itself.
        Fields to be returned after a database insert.
        """
        return [
            field
            for field in self._get_fields(
                forward=True, reverse=False, include_parents=PROXY_PARENTS
            )
            if getattr(field, "db_returning", False)
        ]