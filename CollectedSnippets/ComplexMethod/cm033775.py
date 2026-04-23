def isodate(value, check_deprecation_date=False, is_tombstone=False):
    """Validate a datetime.date or ISO 8601 date string."""
    # datetime.date objects come from YAML dates, these are ok
    if isinstance(value, datetime.date):
        removal_date = value
    else:
        # make sure we have a string
        msg = 'Expected ISO 8601 date string (YYYY-MM-DD), or YAML date'
        if not isinstance(value, str):
            raise Invalid(msg)
        # From Python 3.7 in, there is datetime.date.fromisoformat(). For older versions,
        # we have to do things manually.
        if not re.match('^[0-9]{4}-[0-9]{2}-[0-9]{2}$', value):
            raise Invalid(msg)
        try:
            removal_date = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise Invalid(msg)
    # Make sure date is correct
    today = datetime.date.today()
    if is_tombstone:
        # For a tombstone, the removal date must be in the past
        if today < removal_date:
            raise Invalid(
                'The tombstone removal_date (%s) must not be after today (%s)' % (removal_date, today))
    else:
        # For a deprecation, the removal date must be in the future. Only test this if
        # check_deprecation_date is truish, to avoid checks to suddenly start to fail.
        if check_deprecation_date and today > removal_date:
            raise Invalid(
                'The deprecation removal_date (%s) must be after today (%s)' % (removal_date, today))
    return value