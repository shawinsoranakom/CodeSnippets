def get_finders():
    for finder_path in settings.STATICFILES_FINDERS:
        yield get_finder(finder_path)