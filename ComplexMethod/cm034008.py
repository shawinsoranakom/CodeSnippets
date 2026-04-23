def _configure_auth(url, url_username, url_password, use_gssapi, force_basic_auth, use_netrc):
    headers = {}
    handlers = []

    parsed = urlparse(url)
    if parsed.scheme == 'ftp':
        return url, headers, handlers

    username = url_username
    password = url_password

    if username:
        netloc = parsed.netloc
    elif '@' in parsed.netloc:
        credentials, netloc = parsed.netloc.split('@', 1)
        if ':' in credentials:
            username, password = credentials.split(':', 1)
        else:
            username = credentials
            password = ''
        username = unquote(username)
        password = unquote(password)

        # reconstruct url without credentials
        url = urlunparse(parsed._replace(netloc=netloc))

    if use_gssapi:
        if HTTPGSSAPIAuthHandler:  # type: ignore[truthy-function]
            handlers.append(HTTPGSSAPIAuthHandler(username, password))
        else:
            imp_err_msg = missing_required_lib('gssapi', reason='for use_gssapi=True',
                                               url='https://pypi.org/project/gssapi/')
            raise MissingModuleError(imp_err_msg, import_traceback=GSSAPI_IMP_ERR)

    elif username and not force_basic_auth:
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()

        # this creates a password manager
        passman.add_password(None, netloc, username, password)

        # because we have put None at the start it will always
        # use this username/password combination for  urls
        # for which `theurl` is a super-url
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        digest_authhandler = urllib.request.HTTPDigestAuthHandler(passman)

        # create the AuthHandler
        handlers.append(authhandler)
        handlers.append(digest_authhandler)

    elif username and force_basic_auth:
        headers["Authorization"] = basic_auth_header(username, password)

    elif use_netrc:
        try:
            rc = netrc.netrc(os.environ.get('NETRC'))
            login = rc.authenticators(parsed.hostname)
        except OSError:
            login = None

        if login:
            username, dummy, password = login
            if username and password:
                headers["Authorization"] = basic_auth_header(username, password)

    return url, headers, handlers