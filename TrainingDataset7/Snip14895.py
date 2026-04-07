def _get_next_month(self, date):
        """
        Return the start date of the next interval.

        The interval is defined by start date <= item date < next start date.
        """
        if date.month == 12:
            try:
                return date.replace(year=date.year + 1, month=1, day=1)
            except ValueError:
                raise Http404(_("Date out of range"))
        else:
            return date.replace(month=date.month + 1, day=1)