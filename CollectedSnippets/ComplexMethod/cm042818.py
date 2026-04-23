def fetch_cna():

    def quote_cna(val):
        if '%' in val:
            return val
        return urllib.parse.quote(val)

    if cookies:
        for cookie in cookies:
            if cookie.name == 'cna' and cookie.domain == '.youku.com':
                log.i('Found cna in imported cookies. Use it')
                return quote_cna(cookie.value)
    url = 'http://log.mmstat.com/eg.js'
    req = urllib.request.urlopen(url)
    headers = req.getheaders()
    for header in headers:
        if header[0].lower() == 'set-cookie':
            n_v = header[1].split(';')[0]
            name, value = n_v.split('=')
            if name == 'cna':
                return quote_cna(value)
    log.w('It seems that the client failed to fetch a cna cookie. Please load your own cookie if possible')
    return quote_cna('DOG4EdW4qzsCAbZyXbU+t7Jt')