def get_languages():
    """
    Cache of settings.LANGUAGES in a dictionary for easy lookups by key.
    Convert keys to lowercase as they should be treated as case-insensitive.
    """
    return {key.lower(): value for key, value in dict(settings.LANGUAGES).items()}