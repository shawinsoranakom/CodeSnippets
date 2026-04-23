def preprocess(**kwargs):
            if file_macros and 'macros' not in kwargs:
                kwargs['macros'] = macros
            if file_includes and 'includes' not in kwargs:
                kwargs['includes'] = includes
            if file_incldirs and 'incldirs' not in kwargs:
                kwargs['incldirs'] = incldirs
            if file_same and 'samefiles' not in kwargs:
                kwargs['samefiles'] = samefiles
            kwargs.setdefault('filename', filename)
            with handling_errors(ignore_exc, log_err=log_err):
                return _preprocess(filename, **kwargs)