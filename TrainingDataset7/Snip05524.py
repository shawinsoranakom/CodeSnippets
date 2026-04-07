def is_language_prefix_patterns_used(urlconf):
    """
    Return a tuple of two booleans: (
        `True` if i18n_patterns() (LocalePrefixPattern) is used in the URLconf,
        `True` if the default language should be prefixed
    )
    """
    for url_pattern in get_resolver(urlconf).url_patterns:
        if isinstance(url_pattern.pattern, LocalePrefixPattern):
            return True, url_pattern.pattern.prefix_default_language
    return False, False