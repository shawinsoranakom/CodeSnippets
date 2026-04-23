def post_content(url, headers={}, post_data={}, decoded=True, **kwargs):
    """Post the content of a URL via sending a HTTP POST request.

    Args:
        url: A URL.
        headers: Request headers used by the client.
        decoded: Whether decode the response body using UTF-8 or the charset specified in Content-Type.

    Returns:
        The content as a string.
    """
    if kwargs.get('post_data_raw'):
        logging.debug('post_content: %s\npost_data_raw: %s' % (url, kwargs['post_data_raw']))
    else:
        logging.debug('post_content: %s\npost_data: %s' % (url, post_data))

    req = request.Request(url, headers=headers)
    if cookies:
        # NOTE: Do not use cookies.add_cookie_header(req)
        # #HttpOnly_ cookies were not supported by CookieJar and MozillaCookieJar properly until python 3.10
        # See also:
        # - https://github.com/python/cpython/pull/17471
        # - https://bugs.python.org/issue2190
        # Here we add cookies to the request headers manually
        cookie_strings = []
        for cookie in list(cookies):
            cookie_strings.append(cookie.name + '=' + cookie.value)
        cookie_headers = {'Cookie': '; '.join(cookie_strings)}
        req.headers.update(cookie_headers)
    if kwargs.get('post_data_raw'):
        post_data_enc = bytes(kwargs['post_data_raw'], 'utf-8')
    else:
        post_data_enc = bytes(parse.urlencode(post_data), 'utf-8')
    response = urlopen_with_retry(req, data=post_data_enc)
    data = response.read()

    # Handle HTTP compression for gzip and deflate (zlib)
    content_encoding = response.getheader('Content-Encoding')
    if content_encoding == 'gzip':
        data = ungzip(data)
    elif content_encoding == 'deflate':
        data = undeflate(data)

    # Decode the response body
    if decoded:
        charset = match1(
            response.getheader('Content-Type'), r'charset=([\w-]+)'
        )
        if charset is not None:
            data = data.decode(charset)
        else:
            data = data.decode('utf-8')

    return data