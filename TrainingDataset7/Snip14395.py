def _guess_stylesheet_mimetype(url):
    """
    Return the given stylesheet's mimetype tuple, using a slightly custom
    version of Python's mimetypes.guess_type().
    """
    mimetypedb = mimetypes.MimeTypes()

    # The official mimetype for XSLT files is technically
    # `application/xslt+xml` but as of 2024 almost no browser supports that
    # (they all expect text/xsl). On top of that, windows seems to assume that
    # the type for xsl is text/xml.
    mimetypedb.readfp(StringIO("text/xsl\txsl\ntext/xsl\txslt"))

    return mimetypedb.guess_type(url)