def _reshape_youtube_url(url: str) -> Optional[str]:
    """Return whether URL is any kind of YouTube embed or watch link.  If so,
    reshape URL into an embed link suitable for use in an iframe.

    If not a YouTube URL, return None.

    Parameters
    ----------
        url : str

    Example
    -------
    >>> print(_reshape_youtube_url('https://youtu.be/_T8LGqJtuGc'))

    .. output::
        https://www.youtube.com/embed/_T8LGqJtuGc
    """
    match = YOUTUBE_RE.match(url)
    if match:
        return "https://www.youtube.com/embed/{code}".format(**match.groupdict())
    return None