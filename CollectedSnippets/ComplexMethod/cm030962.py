def open_urlresource(url, *args, **kw):
    import urllib.request, urllib.parse
    from .os_helper import unlink
    try:
        import gzip
    except ImportError:
        gzip = None

    check = kw.pop('check', None)

    filename = urllib.parse.urlparse(url)[2].split('/')[-1] # '/': it's URL!

    fn = os.path.join(TEST_DATA_DIR, filename)

    def check_valid_file(fn):
        f = open(fn, *args, **kw)
        if check is None:
            return f
        elif check(f):
            f.seek(0)
            return f
        f.close()

    if os.path.exists(fn):
        f = check_valid_file(fn)
        if f is not None:
            return f
        unlink(fn)

    # Verify the requirement before downloading the file
    requires('urlfetch')

    if verbose:
        print('\tfetching %s ...' % url, file=get_original_stdout())
    opener = urllib.request.build_opener()
    if gzip:
        opener.addheaders.append(('Accept-Encoding', 'gzip'))
    f = opener.open(url, timeout=INTERNET_TIMEOUT)
    if gzip and f.headers.get('Content-Encoding') == 'gzip':
        f = gzip.GzipFile(fileobj=f)
    try:
        with open(fn, "wb") as out:
            s = f.read()
            while s:
                out.write(s)
                s = f.read()
    finally:
        f.close()

    f = check_valid_file(fn)
    if f is not None:
        return f
    raise TestFailed('invalid resource %r' % fn)