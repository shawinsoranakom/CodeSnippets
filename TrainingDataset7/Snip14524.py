def http_date(epoch_seconds=None):
    """
    Format the time to match the RFC 5322 date format as specified by RFC 9110
    Section 5.6.7.

    `epoch_seconds` is a floating point number expressed in seconds since the
    epoch, in UTC - such as that outputted by time.time(). If set to None, it
    defaults to the current time.

    Output a string in the format 'Wdy, DD Mon YYYY HH:MM:SS GMT'.
    """
    return formatdate(epoch_seconds, usegmt=True)