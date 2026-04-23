def transient_internet(resource_name, *, timeout=_NOT_SET, errnos=()):
    """Return a context manager that raises ResourceDenied when various issues
    with the internet connection manifest themselves as exceptions."""
    import urllib.error
    if timeout is _NOT_SET:
        timeout = support.INTERNET_TIMEOUT

    default_errnos = [
        ('ECONNREFUSED', 111),
        ('ECONNRESET', 104),
        ('EHOSTUNREACH', 113),
        ('ENETUNREACH', 101),
        ('ETIMEDOUT', 110),
        # socket.create_connection() fails randomly with
        # EADDRNOTAVAIL on Travis CI.
        ('EADDRNOTAVAIL', 99),
    ]
    default_gai_errnos = [
        ('EAI_AGAIN', -3),
        ('EAI_FAIL', -4),
        ('EAI_NONAME', -2),
        ('EAI_NODATA', -5),
        # Encountered when trying to resolve IPv6-only hostnames
        ('WSANO_DATA', 11004),
    ]

    denied = support.ResourceDenied("Resource %r is not available" % resource_name)
    captured_errnos = errnos
    gai_errnos = []
    if not captured_errnos:
        captured_errnos = [getattr(errno, name, num)
                           for (name, num) in default_errnos]
        gai_errnos = [getattr(socket, name, num)
                      for (name, num) in default_gai_errnos]

    def filter_error(err):
        n = getattr(err, 'errno', None)
        if (isinstance(err, TimeoutError) or
            (isinstance(err, socket.gaierror) and n in gai_errnos) or
            (isinstance(err, urllib.error.HTTPError) and
             500 <= err.code <= 599) or
            (isinstance(err, urllib.error.URLError) and
                 (("ConnectionRefusedError" in err.reason) or
                  ("TimeoutError" in err.reason) or
                  ("EOFError" in err.reason))) or
            n in captured_errnos):
            if not support.verbose:
                sys.stderr.write(denied.args[0] + "\n")
            raise denied from err

    old_timeout = socket.getdefaulttimeout()
    try:
        if timeout is not None:
            socket.setdefaulttimeout(timeout)
        yield
    except OSError as err:
        # urllib can wrap original socket errors multiple times (!), we must
        # unwrap to get at the original error.
        while True:
            a = err.args
            if len(a) >= 1 and isinstance(a[0], OSError):
                err = a[0]
            # The error can also be wrapped as args[1]:
            #    except socket.error as msg:
            #        raise OSError('socket error', msg) from msg
            elif len(a) >= 2 and isinstance(a[1], OSError):
                err = a[1]
            # The error can also be wrapped as __cause__:
            #    raise URLError(f"ftp error: {exp}") from exp
            elif isinstance(err, urllib.error.URLError) and err.__cause__:
                err = err.__cause__
            else:
                break
        filter_error(err)
        raise
    # XXX should we catch generic exceptions and look for their
    # __cause__ or __context__?
    finally:
        socket.setdefaulttimeout(old_timeout)