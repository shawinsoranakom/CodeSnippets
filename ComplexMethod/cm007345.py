def _quote(s, safe='/'):
            """quote('abc def') -> 'abc%20def'"""

            if not s and s is not None:  # fast path
                return s
            safe = frozenset(safe)
            cachekey = (safe, _always_safe)
            try:
                safe_map = _safemaps[cachekey]
            except KeyError:
                safe = _always_safe | safe
                safe_map = {}
                for i in range(256):
                    c = chr(i)
                    safe_map[c] = (
                        c if (i < 128 and c in safe)
                        else b'%{0:02X}'.format(i))
                _safemaps[cachekey] = safe_map

            if safe.issuperset(s):
                return s
            return ''.join(safe_map[c] for c in s)