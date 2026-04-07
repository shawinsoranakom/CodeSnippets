def check_finders(app_configs, **kwargs):
    """Check all registered staticfiles finders."""
    errors = []
    for finder in get_finders():
        try:
            finder_errors = finder.check()
        except NotImplementedError:
            pass
        else:
            errors.extend(finder_errors)
    return errors