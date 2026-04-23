def _is_pk_set(self, meta=None):
        pk_val = self._get_pk_val(meta)
        return not (
            pk_val is None
            or (isinstance(pk_val, tuple) and any(f is None for f in pk_val))
        )