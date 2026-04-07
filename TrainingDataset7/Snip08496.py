def _datetime_from_timestamp(self, ts):
        """
        If timezone support is enabled, make an aware datetime object in UTC;
        otherwise make a naive one in the local timezone.
        """
        tz = UTC if settings.USE_TZ else None
        return datetime.fromtimestamp(ts, tz=tz)