def psql_escape(query):
    """Replace chars not fit for use in search queries with a single space."""
    query = spec_chars_re.sub(" ", query)
    return normalize_spaces(query)