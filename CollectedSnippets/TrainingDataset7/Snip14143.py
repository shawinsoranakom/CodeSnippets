def check_errors(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        global _exception
        try:
            fn(*args, **kwargs)
        except Exception as e:
            _exception = sys.exc_info()

            et, ev, tb = _exception

            if getattr(ev, "filename", None) is None:
                # get the filename from the last item in the stack
                filename = traceback.extract_tb(tb)[-1][0]
            else:
                filename = ev.filename

            if filename not in _error_files:
                _error_files.append(filename)
            if _url_module_exception is not None:
                raise e from _url_module_exception

            raise e

    return wrapper