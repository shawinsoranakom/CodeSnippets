def cookie_to_dict(cookie):
    cookie_dict = {
        'name': cookie.name,
        'value': cookie.value,
    }
    if cookie.port_specified:
        cookie_dict['port'] = cookie.port
    if cookie.domain_specified:
        cookie_dict['domain'] = cookie.domain
    if cookie.path_specified:
        cookie_dict['path'] = cookie.path
    if cookie.expires is not None:
        cookie_dict['expires'] = cookie.expires
    if cookie.secure is not None:
        cookie_dict['secure'] = cookie.secure
    if cookie.discard is not None:
        cookie_dict['discard'] = cookie.discard
    with contextlib.suppress(TypeError):
        if (cookie.has_nonstandard_attr('httpOnly')
                or cookie.has_nonstandard_attr('httponly')
                or cookie.has_nonstandard_attr('HttpOnly')):
            cookie_dict['httponly'] = True
    return cookie_dict