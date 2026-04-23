def _is_local_authority(authority, resolve):
    # Compare hostnames
    if not authority or authority == 'localhost':
        return True
    try:
        hostname = socket.gethostname()
    except (socket.gaierror, AttributeError):
        pass
    else:
        if authority == hostname:
            return True
    # Compare IP addresses
    if not resolve:
        return False
    try:
        address = socket.gethostbyname(authority)
    except (socket.gaierror, AttributeError, UnicodeEncodeError):
        return False
    return address in FileHandler().get_names()