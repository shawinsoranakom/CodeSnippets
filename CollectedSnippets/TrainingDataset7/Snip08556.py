def load_handler(path, *args, **kwargs):
    """
    Given a path to a handler, return an instance of that handler.

    E.g.::
        >>> from django.http import HttpRequest
        >>> request = HttpRequest()
        >>> load_handler(
        ...     'django.core.files.uploadhandler.TemporaryFileUploadHandler',
        ...     request,
        ... )
        <TemporaryFileUploadHandler object at 0x...>
    """
    return import_string(path)(*args, **kwargs)