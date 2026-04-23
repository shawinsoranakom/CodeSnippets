def get_link_preview_from_url(url, request_session=None):
    """
    Get the Open Graph properties of an url. (https://ogp.me/)
    If the url leads directly to an image mimetype, return
    the url as preview image else retrieve the properties from
    the html page.

    Using a stream request to prevent loading the whole page
    as those properties are declared in the <head> tag.

    The request session is optional as in some cases using
    a session could be beneficial performance wise
    (e.g. a lot of url could have the same domain).
    """
    # Some websites are blocking non browser user agent.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
        'Odoo-Link-Preview': 'True',  # Used to identify coming from the link previewer
    }
    try:
        if request_session:
            response = request_session.get(url, timeout=3, headers=headers, allow_redirects=True, stream=True)
        else:
            response = requests.get(url, timeout=3, headers=headers, allow_redirects=True, stream=True)
    except requests.exceptions.RequestException:
        return False
    except LocationParseError:
        return False
    if not response.ok or not response.headers.get('Content-Type'):
        return False
    # Content-Type header can return a charset, but we just need the
    # mimetype (eg: image/jpeg;charset=ISO-8859-1)
    content_type = response.headers['Content-Type'].split(';')
    if response.headers['Content-Type'].startswith('image/'):
        return {
            'image_mimetype': content_type[0],
            'og_image': url, # If the url mimetype is already an image type, set url as preview image
            'source_url': url,
        }
    elif response.headers['Content-Type'].startswith('text/html'):
        return get_link_preview_from_html(url, response)
    return False