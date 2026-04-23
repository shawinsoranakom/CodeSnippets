def heuristic_log_sanitize(data, no_log_values=None):
    """ Remove strings that look like passwords from log messages """
    # Currently filters:
    # user:pass@foo/whatever and http://username:pass@wherever/foo
    # This code has false positives and consumes parts of logs that are
    # not passwds

    # begin: start of a passwd containing string
    # end: end of a passwd containing string
    # sep: char between user and passwd
    # prev_begin: where in the overall string to start a search for
    #   a passwd
    # sep_search_end: where in the string to end a search for the sep
    data = to_native(data)

    output = []
    begin = len(data)
    prev_begin = begin
    sep = 1
    while sep:
        # Find the potential end of a passwd
        try:
            end = data.rindex('@', 0, begin)
        except ValueError:
            # No passwd in the rest of the data
            output.insert(0, data[0:begin])
            break

        # Search for the beginning of a passwd
        sep = None
        sep_search_end = end
        while not sep:
            # URL-style username+password
            try:
                begin = data.rindex('://', 0, sep_search_end)
            except ValueError:
                # No url style in the data, check for ssh style in the
                # rest of the string
                begin = 0
            # Search for separator
            try:
                sep = data.index(':', begin + 3, end)
            except ValueError:
                # No separator; choices:
                if begin == 0:
                    # Searched the whole string so there's no password
                    # here.  Return the remaining data
                    output.insert(0, data[0:prev_begin])
                    break
                # Search for a different beginning of the password field.
                sep_search_end = begin
                continue
        if sep:
            # Password was found; remove it.
            output.insert(0, data[end:prev_begin])
            output.insert(0, '********')
            output.insert(0, data[begin:sep + 1])
            prev_begin = begin

    output = ''.join(output)
    if no_log_values:
        output = remove_values(output, no_log_values)
    return output