def _get_compatible_backends(request, **credentials):
    for backend, backend_path in _get_backends(return_tuples=True):
        backend_signature = signature(backend.authenticate)
        try:
            backend_signature.bind(request, **credentials)
        except TypeError:
            # This backend doesn't accept these credentials as arguments. Try
            # the next one.
            continue
        yield backend, backend_path