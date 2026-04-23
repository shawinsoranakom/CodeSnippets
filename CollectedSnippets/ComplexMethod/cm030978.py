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