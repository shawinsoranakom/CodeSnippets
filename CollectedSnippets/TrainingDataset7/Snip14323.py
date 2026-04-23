def r(self):
        "RFC 5322 formatted date; e.g. 'Thu, 21 Dec 2000 16:01:07 +0200'"
        value = self.data
        if not isinstance(value, datetime):
            # Assume midnight in default timezone if datetime.date provided.
            default_timezone = get_default_timezone()
            value = datetime.combine(value, time.min).replace(tzinfo=default_timezone)
        elif is_naive(value):
            value = make_aware(value, timezone=self.timezone)
        return format_datetime_rfc5322(value)