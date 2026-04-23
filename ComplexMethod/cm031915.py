def handling_errors(ignore_exc=None, *, log_err=None):
    try:
        yield
    except _errors.OSMismatchError as exc:
        if not ignore_exc(exc):
            raise  # re-raise
        if log_err is not None:
            log_err(f'<OS mismatch (expected {" or ".join(exc.expected)})>')
        return None
    except _errors.MissingDependenciesError as exc:
        if not ignore_exc(exc):
            raise  # re-raise
        if log_err is not None:
            log_err(f'<missing dependency {exc.missing}')
        return None
    except _errors.ErrorDirectiveError as exc:
        if not ignore_exc(exc):
            raise  # re-raise
        if log_err is not None:
            log_err(exc)
        return None