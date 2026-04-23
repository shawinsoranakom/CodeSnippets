def url_to_module(url):
    try:
        video_host = r1(r'https?://([^/]+)/', url)
        video_url = r1(r'https?://[^/]+(.*)', url)
        assert video_host and video_url
    except AssertionError:
        url = google_search(url)
        video_host = r1(r'https?://([^/]+)/', url)
        video_url = r1(r'https?://[^/]+(.*)', url)

    if video_host.endswith('.com.cn') or video_host.endswith('.ac.cn'):
        video_host = video_host[:-3]
    domain = r1(r'(\.[^.]+\.[^.]+)$', video_host) or video_host
    assert domain, 'unsupported url: ' + url

    # all non-ASCII code points must be quoted (percent-encoded UTF-8)
    url = ''.join([ch if ord(ch) in range(128) else parse.quote(ch) for ch in url])
    video_host = r1(r'https?://([^/]+)/', url)
    video_url = r1(r'https?://[^/]+(.*)', url)

    k = r1(r'([^.]+)', domain)
    if k in SITES:
        return (
            import_module('.'.join(['you_get', 'extractors', SITES[k]])),
            url
        )
    else:
        try:
            try:
                location = get_location(url) # t.co isn't happy with fake_headers
            except:
                location = get_location(url, headers=fake_headers)
        except:
            location = get_location(url, headers=fake_headers, get_method='GET')

        if location and location != url and not location.startswith('/'):
            return url_to_module(location)
        else:
            return import_module('you_get.extractors.universal'), url