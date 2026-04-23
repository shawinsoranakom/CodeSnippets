def _get_next_day(self, date):
        """
        Return the start date of the next interval.

        The interval is defined by start date <= item date < next start date.
        """
        return date + datetime.timedelta(days=1)