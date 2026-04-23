def url2pathname(url, *, require_scheme=False, resolve_host=False):
    """Convert the given file URL to a local file system path.

    The 'file:' scheme prefix must be omitted unless *require_scheme*
    is set to true.

    The URL authority may be resolved with gethostbyname() if
    *resolve_host* is set to true.
    """
    if not require_scheme:
        url = 'file:' + url
    scheme, authority, url = urlsplit(url)[:3]  # Discard query and fragment.
    if scheme != 'file':
        raise URLError("URL is missing a 'file:' scheme")
    if os.name == 'nt':
        if authority[1:2] == ':':
            # e.g. file://c:/file.txt
            url = authority + url
        elif not _is_local_authority(authority, resolve_host):
            # e.g. file://server/share/file.txt
            url = '//' + authority + url
        elif url[:3] == '///':
            # e.g. file://///server/share/file.txt
            url = url[1:]
        else:
            if url[:1] == '/' and url[2:3] in (':', '|'):
                # Skip past extra slash before DOS drive in URL path.
                url = url[1:]
            if url[1:2] == '|':
                # Older URLs use a pipe after a drive letter
                url = url[:1] + ':' + url[2:]
        url = url.replace('/', '\\')
    elif not _is_local_authority(authority, resolve_host):
        raise URLError("file:// scheme is supported only on localhost")
    encoding = sys.getfilesystemencoding()
    errors = sys.getfilesystemencodeerrors()
    return unquote(url, encoding=encoding, errors=errors)