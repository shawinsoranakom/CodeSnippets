def _format_params(self, params):
        try:
            return {k: OracleParam(v, self, True) for k, v in params.items()}
        except AttributeError:
            return tuple(OracleParam(p, self, True) for p in params)