def _extract_firefox_cookies(profile, container, logger):
    MAX_SUPPORTED_DB_SCHEMA_VERSION = 17

    logger.info('Extracting cookies from firefox')
    if not sqlite3:
        logger.warning('Cannot extract cookies from firefox without sqlite3 support. '
                       'Please use a Python interpreter compiled with sqlite3 support')
        return YoutubeDLCookieJar()

    if profile is None:
        search_roots = list(_firefox_browser_dirs())
    elif _is_path(profile):
        search_roots = [profile]
    else:
        search_roots = [os.path.join(path, profile) for path in _firefox_browser_dirs()]
    search_root = ', '.join(map(repr, search_roots))

    cookie_database_path = _newest(_firefox_cookie_dbs(search_roots))
    if cookie_database_path is None:
        raise FileNotFoundError(f'could not find firefox cookies database in {search_root}')
    logger.debug(f'Extracting cookies from: "{cookie_database_path}"')

    container_id = None
    if container not in (None, 'none'):
        containers_path = os.path.join(os.path.dirname(cookie_database_path), 'containers.json')
        if not os.path.isfile(containers_path) or not os.access(containers_path, os.R_OK):
            raise FileNotFoundError(f'could not read containers.json in {search_root}')
        with open(containers_path, encoding='utf8') as containers:
            identities = json.load(containers).get('identities', [])
        container_id = next((context.get('userContextId') for context in identities if container in (
            context.get('name'),
            try_call(lambda: re.fullmatch(r'userContext([^\.]+)\.label', context['l10nID']).group()),
        )), None)
        if not isinstance(container_id, int):
            raise ValueError(f'could not find firefox container "{container}" in containers.json')

    with tempfile.TemporaryDirectory(prefix='yt_dlp') as tmpdir:
        cursor = _open_database_copy(cookie_database_path, tmpdir)
        with contextlib.closing(cursor.connection):
            db_schema_version = cursor.execute('PRAGMA user_version;').fetchone()[0]
            if db_schema_version > MAX_SUPPORTED_DB_SCHEMA_VERSION:
                logger.warning(f'Possibly unsupported firefox cookies database version: {db_schema_version}')
            else:
                logger.debug(f'Firefox cookies database version: {db_schema_version}')
            if isinstance(container_id, int):
                logger.debug(
                    f'Only loading cookies from firefox container "{container}", ID {container_id}')
                cursor.execute(
                    'SELECT host, name, value, path, expiry, isSecure FROM moz_cookies WHERE originAttributes LIKE ? OR originAttributes LIKE ?',
                    (f'%userContextId={container_id}', f'%userContextId={container_id}&%'))
            elif container == 'none':
                logger.debug('Only loading cookies not belonging to any container')
                cursor.execute(
                    'SELECT host, name, value, path, expiry, isSecure FROM moz_cookies WHERE NOT INSTR(originAttributes,"userContextId=")')
            else:
                cursor.execute('SELECT host, name, value, path, expiry, isSecure FROM moz_cookies')
            jar = YoutubeDLCookieJar()
            with _create_progress_bar(logger) as progress_bar:
                table = cursor.fetchall()
                total_cookie_count = len(table)
                for i, (host, name, value, path, expiry, is_secure) in enumerate(table):
                    progress_bar.print(f'Loading cookie {i: 6d}/{total_cookie_count: 6d}')
                    # FF142 upgraded cookies DB to schema version 16 and started using milliseconds for cookie expiry
                    # Ref: https://github.com/mozilla-firefox/firefox/commit/5869af852cd20425165837f6c2d9971f3efba83d
                    if db_schema_version >= 16 and expiry is not None:
                        expiry /= 1000
                    cookie = http.cookiejar.Cookie(
                        version=0, name=name, value=value, port=None, port_specified=False,
                        domain=host, domain_specified=bool(host), domain_initial_dot=host.startswith('.'),
                        path=path, path_specified=bool(path), secure=is_secure, expires=expiry, discard=False,
                        comment=None, comment_url=None, rest={})
                    jar.set_cookie(cookie)
            logger.info(f'Extracted {len(jar)} cookies from firefox')
            return jar