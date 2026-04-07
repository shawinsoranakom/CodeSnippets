def extract_token_from_url(url):
    token_search = re.search(r"/reset/.*/(.+?)/", url)
    if token_search:
        return token_search[1]