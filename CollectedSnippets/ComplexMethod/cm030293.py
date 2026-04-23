def read_environ():
    """Read environment, fixing HTTP variables"""
    enc = sys.getfilesystemencoding()
    esc = 'surrogateescape'
    try:
        ''.encode('utf-8', esc)
    except LookupError:
        esc = 'replace'
    environ = {}

    # Take the basic environment from native-unicode os.environ. Attempt to
    # fix up the variables that come from the HTTP request to compensate for
    # the bytes->unicode decoding step that will already have taken place.
    for k, v in os.environ.items():
        if _needs_transcode(k):

            # On win32, the os.environ is natively Unicode. Different servers
            # decode the request bytes using different encodings.
            if sys.platform == 'win32':
                software = os.environ.get('SERVER_SOFTWARE', '').lower()

                # On IIS, the HTTP request will be decoded as UTF-8 as long
                # as the input is a valid UTF-8 sequence. Otherwise it is
                # decoded using the system code page (mbcs), with no way to
                # detect this has happened. Because UTF-8 is the more likely
                # encoding, and mbcs is inherently unreliable (an mbcs string
                # that happens to be valid UTF-8 will not be decoded as mbcs)
                # always recreate the original bytes as UTF-8.
                if software.startswith('microsoft-iis/'):
                    v = v.encode('utf-8').decode('iso-8859-1')

                # Apache mod_cgi writes bytes-as-unicode (as if ISO-8859-1) direct
                # to the Unicode environ. No modification needed.
                elif software.startswith('apache/'):
                    pass

                # Python 3's http.server.CGIHTTPRequestHandler decodes
                # using the urllib.unquote default of UTF-8, amongst other
                # issues. While the CGI handler is removed in 3.15, this
                # is kept for legacy reasons.
                elif (
                    software.startswith('simplehttp/')
                    and 'python/3' in software
                ):
                    v = v.encode('utf-8').decode('iso-8859-1')

                # For other servers, guess that they have written bytes to
                # the environ using stdio byte-oriented interfaces, ending up
                # with the system code page.
                else:
                    v = v.encode(enc, 'replace').decode('iso-8859-1')

            # Recover bytes from unicode environ, using surrogate escapes
            # where available (Python 3.1+).
            else:
                v = v.encode(enc, esc).decode('iso-8859-1')

        environ[k] = v
    return environ