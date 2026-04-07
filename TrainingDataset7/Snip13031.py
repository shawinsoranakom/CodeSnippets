def _get_failure_view():
    """Return the view to be used for CSRF rejections."""
    return get_callable(settings.CSRF_FAILURE_VIEW)