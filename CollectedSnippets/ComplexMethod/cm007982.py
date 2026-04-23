def _extract_chrome_cookies(browser_name, profile, keyring, logger):
    logger.info(f'Extracting cookies from {browser_name}')

    if not sqlite3:
        logger.warning(f'Cannot extract cookies from {browser_name} without sqlite3 support. '
                       'Please use a Python interpreter compiled with sqlite3 support')
        return YoutubeDLCookieJar()

    config = _get_chromium_based_browser_settings(browser_name)

    if profile is None:
        search_root = config['browser_dir']
    elif _is_path(profile):
        search_root = profile
        config['browser_dir'] = os.path.dirname(profile) if config['supports_profiles'] else profile
    else:
        if config['supports_profiles']:
            search_root = os.path.join(config['browser_dir'], profile)
        else:
            logger.error(f'{browser_name} does not support profiles')
            search_root = config['browser_dir']

    cookie_database_path = _newest(_find_files(search_root, 'Cookies', logger))
    if cookie_database_path is None:
        raise FileNotFoundError(f'could not find {browser_name} cookies database in "{search_root}"')
    logger.debug(f'Extracting cookies from: "{cookie_database_path}"')

    with tempfile.TemporaryDirectory(prefix='yt_dlp') as tmpdir:
        cursor = None
        try:
            cursor = _open_database_copy(cookie_database_path, tmpdir)

            # meta_version is necessary to determine if we need to trim the hash prefix from the cookies
            # Ref: https://chromium.googlesource.com/chromium/src/+/b02dcebd7cafab92770734dc2bc317bd07f1d891/net/extras/sqlite/sqlite_persistent_cookie_store.cc#223
            meta_version = int(cursor.execute('SELECT value FROM meta WHERE key = "version"').fetchone()[0])
            decryptor = get_cookie_decryptor(
                config['browser_dir'], config['keyring_name'], logger,
                keyring=keyring, meta_version=meta_version)

            cursor.connection.text_factory = bytes
            column_names = _get_column_names(cursor, 'cookies')
            secure_column = 'is_secure' if 'is_secure' in column_names else 'secure'
            cursor.execute(f'SELECT host_key, name, value, encrypted_value, path, expires_utc, {secure_column} FROM cookies')
            jar = YoutubeDLCookieJar()
            failed_cookies = 0
            unencrypted_cookies = 0
            with _create_progress_bar(logger) as progress_bar:
                table = cursor.fetchall()
                total_cookie_count = len(table)
                for i, line in enumerate(table):
                    progress_bar.print(f'Loading cookie {i: 6d}/{total_cookie_count: 6d}')
                    is_encrypted, cookie = _process_chrome_cookie(decryptor, *line)
                    if not cookie:
                        failed_cookies += 1
                        continue
                    elif not is_encrypted:
                        unencrypted_cookies += 1
                    jar.set_cookie(cookie)
            if failed_cookies > 0:
                failed_message = f' ({failed_cookies} could not be decrypted)'
            else:
                failed_message = ''
            logger.info(f'Extracted {len(jar)} cookies from {browser_name}{failed_message}')
            counts = decryptor._cookie_counts.copy()
            counts['unencrypted'] = unencrypted_cookies
            logger.debug(f'cookie version breakdown: {counts}')
            return jar
        except PermissionError as error:
            if os.name == 'nt' and error.errno == 13:
                message = 'Could not copy Chrome cookie database. See  https://github.com/yt-dlp/yt-dlp/issues/7271  for more info'
                logger.error(message)
                raise DownloadError(message)  # force exit
            raise
        finally:
            if cursor is not None:
                cursor.connection.close()