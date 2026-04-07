def rfc2822_date(date):
    if not isinstance(date, datetime.datetime):
        date = datetime.datetime.combine(date, datetime.time())
    return email.utils.format_datetime(date)