def _odoo_guess_mimetype(bin_data: bytes, default='application/octet-stream'):
    """ Attempts to guess the mime type of the provided binary data, similar
    to but significantly more limited than libmagic

    :param bin_data: binary data to try and guess a mime type for
    :returns: matched mimetype or ``application/octet-stream`` if none matched
    """
    # by default, guess the type using the magic number of file hex signature (like magic, but more limited)
    # see http://www.filesignatures.net/ for file signatures
    for entry in _mime_mappings:
        for signature in entry.signatures:
            if bin_data.startswith(signature):
                for discriminant in entry.discriminants:
                    try:
                        guess = discriminant(bin_data)
                        if guess: return guess
                    except Exception:
                        # log-and-next
                        _logger_guess_mimetype.warning(
                            "Sub-checker '%s' of type '%s' failed",
                            discriminant.__name__, entry.mimetype,
                            exc_info=True
                        )
                # if no discriminant or no discriminant matches, return
                # primary mime type
                return entry.mimetype
    try:
        if bin_data and all(c >= ' ' or c in '\t\n\r' for c in bin_data[:1024].decode()):
            return 'text/plain'
    except ValueError:
        pass
    return default