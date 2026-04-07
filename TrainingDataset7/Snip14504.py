def urlize(text, trim_url_limit=None, nofollow=False, autoescape=False):
    return urlizer(
        text, trim_url_limit=trim_url_limit, nofollow=nofollow, autoescape=autoescape
    )