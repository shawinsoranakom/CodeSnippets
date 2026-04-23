def _get_next_week(self, date):
        """
        Return the start date of the next interval.

        The interval is defined by start date <= item date < next start date.
        """
        try:
            return date + datetime.timedelta(days=7 - self._get_weekday(date))
        except OverflowError:
            raise Http404(_("Date out of range"))