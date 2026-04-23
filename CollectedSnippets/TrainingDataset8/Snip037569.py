def _get_embed_url(url: str) -> str:
    parsed_url = urllib.parse.urlparse(url)

    # Plotly's embed URL is the normal URL plus ".embed".
    # (Note that our use namedtuple._replace is fine because that's not a
    # private method! It just has an underscore to avoid clashing with the
    # tuple field names)
    parsed_embed_url = parsed_url._replace(path=parsed_url.path + ".embed")

    return urllib.parse.urlunparse(parsed_embed_url)