def __init__(
        self,
        title,
        link,
        description,
        language=None,
        author_email=None,
        author_name=None,
        author_link=None,
        subtitle=None,
        categories=None,
        feed_url=None,
        feed_copyright=None,
        feed_guid=None,
        ttl=None,
        stylesheets=None,
        **kwargs,
    ):
        def to_str(s):
            return str(s) if s is not None else s

        def to_stylesheet(s):
            return s if isinstance(s, Stylesheet) else Stylesheet(s)

        categories = categories and [str(c) for c in categories]

        if stylesheets is not None:
            if isinstance(stylesheets, (Stylesheet, str)):
                raise TypeError(
                    f"stylesheets should be a list, not {stylesheets.__class__}"
                )
            stylesheets = [to_stylesheet(s) for s in stylesheets]

        self.feed = {
            "title": to_str(title),
            "link": iri_to_uri(link),
            "description": to_str(description),
            "language": to_str(language),
            "author_email": to_str(author_email),
            "author_name": to_str(author_name),
            "author_link": iri_to_uri(author_link),
            "subtitle": to_str(subtitle),
            "categories": categories or (),
            "feed_url": iri_to_uri(feed_url),
            "feed_copyright": to_str(feed_copyright),
            "id": feed_guid or link,
            "ttl": to_str(ttl),
            "stylesheets": stylesheets,
            **kwargs,
        }
        self.items = []