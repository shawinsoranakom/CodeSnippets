def fetch_url(module, url, data=None, headers=None, method=None,
              use_proxy=None, force=False, last_mod_time=None, timeout=10,
              use_gssapi=False, unix_socket=None, ca_path=None, cookies=None, unredirected_headers=None,
              decompress=True, ciphers=None, use_netrc=True):
    """Sends a request via HTTP(S) or FTP (needs the module as parameter)

    :arg module: The AnsibleModule (used to get username, password etc. (s.b.).
    :arg url:             The url to use.

    :kwarg data:          The data to be sent (in case of POST/PUT).
    :kwarg headers:       A dict with the request headers.
    :kwarg method:        "POST", "PUT", etc.
    :kwarg use_proxy:     (optional) whether or not to use proxy (Default: True)
    :kwarg boolean force: If True: Do not get a cached copy (Default: False)
    :kwarg last_mod_time: Default: None
    :kwarg int timeout:   Default: 10
    :kwarg boolean use_gssapi:   Default: False
    :kwarg unix_socket: (optional) String of file system path to unix socket file to use when establishing
        connection to the provided url
    :kwarg ca_path: (optional) String of file system path to CA cert bundle to use
    :kwarg cookies: (optional) CookieJar object to send with the request
    :kwarg unredirected_headers: (optional) A list of headers to not attach on a redirected request
    :kwarg decompress: (optional) Whether to attempt to decompress gzip content-encoded responses
    :kwarg cipher: (optional) List of ciphers to use
    :kwarg boolean use_netrc: (optional) If False: Ignores login and password in ~/.netrc file (Default: True)

    :returns: A tuple of (**response**, **info**). Use ``response.read()`` to read the data.
        The **info** contains the 'status' and other meta data. When a HttpError (status >= 400)
        occurred then ``info['body']`` contains the error response data::

    Example::

        data={...}
        resp, info = fetch_url(module,
                               "http://example.com",
                               data=json.dumps(data),
                               headers={'Content-type': 'application/json'},
                               method="POST")
        status_code = info["status"]
        body = resp.read()
        if status_code >= 400 :
            body = info['body']
    """

    if not HAS_GZIP:
        module.fail_json(msg=GzipDecodedReader.missing_gzip_error())

    # ensure we use proper tempdir
    old_tempdir = tempfile.tempdir
    tempfile.tempdir = module.tmpdir

    # Get validate_certs from the module params
    validate_certs = module.params.get('validate_certs', True)

    if use_proxy is None:
        use_proxy = module.params.get('use_proxy', True)

    username = module.params.get('url_username', '')
    password = module.params.get('url_password', '')
    http_agent = module.params.get('http_agent', get_user_agent())
    force_basic_auth = module.params.get('force_basic_auth', '')

    follow_redirects = module.params.get('follow_redirects', 'urllib2')

    client_cert = module.params.get('client_cert')
    client_key = module.params.get('client_key')
    use_gssapi = module.params.get('use_gssapi', use_gssapi)

    if not isinstance(cookies, cookiejar.CookieJar):
        cookies = cookiejar.CookieJar()

    r = None
    info = dict(url=url, status=-1)
    try:
        r = open_url(url, data=data, headers=headers, method=method,
                     use_proxy=use_proxy, force=force, last_mod_time=last_mod_time, timeout=timeout,
                     validate_certs=validate_certs, url_username=username,
                     url_password=password, http_agent=http_agent, force_basic_auth=force_basic_auth,
                     follow_redirects=follow_redirects, client_cert=client_cert,
                     client_key=client_key, cookies=cookies, use_gssapi=use_gssapi,
                     unix_socket=unix_socket, ca_path=ca_path, unredirected_headers=unredirected_headers,
                     decompress=decompress, ciphers=ciphers, use_netrc=use_netrc)
        # Lowercase keys, to conform to py2 behavior
        info.update({k.lower(): v for k, v in r.info().items()})

        # Don't be lossy, append header values for duplicate headers
        temp_headers = {}
        for name, value in r.headers.items():
            # The same as above, lower case keys to match py2 behavior, and create more consistent results
            name = name.lower()
            if name in temp_headers:
                temp_headers[name] = ', '.join((temp_headers[name], value))
            else:
                temp_headers[name] = value
        info.update(temp_headers)

        # parse the cookies into a nice dictionary
        cookie_list = []
        cookie_dict = {}
        # Python sorts cookies in order of most specific (ie. longest) path first. See ``CookieJar._cookie_attrs``
        # Cookies with the same path are reversed from response order.
        # This code makes no assumptions about that, and accepts the order given by python
        for cookie in cookies:
            cookie_dict[cookie.name] = cookie.value
            cookie_list.append((cookie.name, cookie.value))
        info['cookies_string'] = '; '.join('%s=%s' % c for c in cookie_list)

        info['cookies'] = cookie_dict
        # finally update the result with a message about the fetch
        info.update(dict(msg="OK (%s bytes)" % r.headers.get('Content-Length', 'unknown'), url=r.geturl(), status=r.code))
    except (ConnectionError, ValueError) as e:
        module.fail_json(msg=to_native(e), **info)
    except MissingModuleError as e:
        module.fail_json(msg=to_text(e))
    except urllib.error.HTTPError as e:
        r = e
        try:
            if e.fp is None:
                # Certain HTTPError objects may not have the ability to call ``.read()`` on Python 3
                # This is not handled gracefully in Python 3, and instead an exception is raised from
                # tempfile, due to ``urllib.response.addinfourl`` not being initialized
                raise AttributeError
            body = e.read()
        except AttributeError:
            body = ''
        else:
            e.close()

        # Try to add exception info to the output but don't fail if we can't
        try:
            # Lowercase keys, to conform to py2 behavior, so that py3 and py2 are predictable
            info.update({k.lower(): v for k, v in e.info().items()})
        except Exception:
            pass

        info.update({'msg': to_native(e), 'body': body, 'status': e.code})

    except urllib.error.URLError as e:
        code = int(getattr(e, 'code', -1))
        info.update(dict(msg="Request failed: %s" % to_native(e), status=code))
    except OSError as ex:
        info.update(dict(msg=f"Connection failure: {ex}", status=-1))
    except http.client.BadStatusLine as e:
        info.update(dict(msg="Connection failure: connection was closed before a valid response was received: %s" % to_native(e.line), status=-1))
    except Exception as ex:
        info.update(dict(msg="An unknown error occurred: %s" % to_native(ex), status=-1, exception=traceback.format_exc()))
    finally:
        tempfile.tempdir = old_tempdir

    return r, info