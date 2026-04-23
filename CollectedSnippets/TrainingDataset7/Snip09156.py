def timezone(self):
        """
        Return a tzinfo of the database connection time zone.

        This is only used when time zone support is enabled. When a datetime is
        read from the database, it is always returned in this time zone.

        When the database backend supports time zones, it doesn't matter which
        time zone Django uses, as long as aware datetimes are used everywhere.
        Other users connecting to the database can choose their own time zone.

        When the database backend doesn't support time zones, the time zone
        Django uses may be constrained by the requirements of other users of
        the database.
        """
        if not settings.USE_TZ:
            return None
        elif self.settings_dict["TIME_ZONE"] is None:
            return datetime.UTC
        else:
            return zoneinfo.ZoneInfo(self.settings_dict["TIME_ZONE"])