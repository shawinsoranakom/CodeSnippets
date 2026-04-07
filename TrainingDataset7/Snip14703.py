def translation(language):
    """
    Return a translation object in the default 'django' domain.
    """
    if language not in _translations:
        _translations[language] = DjangoTranslation(language)
    return _translations[language]