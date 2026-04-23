def _format_import_error(self, error_type, error_msg, error_params=(), error_args=None):
        # sanitize error params for later formatting by the import system
        sanitize = lambda p: p.replace('%', '%%') if isinstance(p, str) else p
        if error_params:
            if isinstance(error_params, str):
                error_params = sanitize(error_params)
            elif isinstance(error_params, dict):
                error_params = {k: sanitize(v) for k, v in error_params.items()}
            elif isinstance(error_params, tuple):
                error_params = tuple(sanitize(v) for v in error_params)
        return error_type(error_msg % error_params, error_args)