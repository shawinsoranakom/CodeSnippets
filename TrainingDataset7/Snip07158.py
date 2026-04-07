def srid(self):
        "Return the SRID of top-level authority, or None if undefined."
        try:
            return int(self.auth_code(target=None))
        except (TypeError, ValueError):
            return None