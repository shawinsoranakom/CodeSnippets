def _index(self, obj, idx, allow_undefined=None):
        if idx == 'length' and isinstance(obj, list):
            return len(obj)
        try:
            return obj[int(idx)] if isinstance(obj, list) else obj[compat_str(idx)]
        except (TypeError, KeyError, IndexError, ValueError) as e:
            # allow_undefined is None gives correct behaviour
            if allow_undefined or (
                    allow_undefined is None and not isinstance(e, TypeError)):
                return JS_Undefined
            raise self.Exception('Cannot get index {idx!r:.100}'.format(**locals()), expr=repr(obj), cause=e)