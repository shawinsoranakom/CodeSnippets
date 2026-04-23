def check_environ(environ):
    assert_(type(environ) is dict,
        "Environment is not of the right type: %r (environment: %r)"
        % (type(environ), environ))

    for key in ['REQUEST_METHOD', 'SERVER_NAME', 'SERVER_PORT',
                'wsgi.version', 'wsgi.input', 'wsgi.errors',
                'wsgi.multithread', 'wsgi.multiprocess',
                'wsgi.run_once']:
        assert_(key in environ,
            "Environment missing required key: %r" % (key,))

    for key in ['HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH']:
        assert_(key not in environ,
            "Environment should not have the key: %s "
            "(use %s instead)" % (key, key[5:]))

    if 'QUERY_STRING' not in environ:
        warnings.warn(
            'QUERY_STRING is not in the WSGI environment; the cgi '
            'module will use sys.argv when this variable is missing, '
            'so application errors are more likely',
            WSGIWarning)

    for key in environ.keys():
        if '.' in key:
            # Extension, we don't care about its type
            continue
        assert_(type(environ[key]) is str,
            "Environmental variable %s is not a string: %r (value: %r)"
            % (key, type(environ[key]), environ[key]))

    assert_(type(environ['wsgi.version']) is tuple,
        "wsgi.version should be a tuple (%r)" % (environ['wsgi.version'],))
    assert_(environ['wsgi.url_scheme'] in ('http', 'https'),
        "wsgi.url_scheme unknown: %r" % environ['wsgi.url_scheme'])

    check_input(environ['wsgi.input'])
    check_errors(environ['wsgi.errors'])

    # @@: these need filling out:
    if environ['REQUEST_METHOD'] not in (
        'GET', 'HEAD', 'POST', 'OPTIONS', 'PATCH', 'PUT', 'DELETE', 'TRACE'):
        warnings.warn(
            "Unknown REQUEST_METHOD: %r" % environ['REQUEST_METHOD'],
            WSGIWarning)

    assert_(not environ.get('SCRIPT_NAME')
            or environ['SCRIPT_NAME'].startswith('/'),
        "SCRIPT_NAME doesn't start with /: %r" % environ['SCRIPT_NAME'])
    assert_(not environ.get('PATH_INFO')
            or environ['PATH_INFO'].startswith('/'),
        "PATH_INFO doesn't start with /: %r" % environ['PATH_INFO'])
    if environ.get('CONTENT_LENGTH'):
        assert_(int(environ['CONTENT_LENGTH']) >= 0,
            "Invalid CONTENT_LENGTH: %r" % environ['CONTENT_LENGTH'])

    if not environ.get('SCRIPT_NAME'):
        assert_('PATH_INFO' in environ,
            "One of SCRIPT_NAME or PATH_INFO are required (PATH_INFO "
            "should at least be '/' if SCRIPT_NAME is empty)")
    assert_(environ.get('SCRIPT_NAME') != '/',
        "SCRIPT_NAME cannot be '/'; it should instead be '', and "
        "PATH_INFO should be '/'")