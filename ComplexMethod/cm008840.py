def decode(self, s):
        if self.transform_source:
            s = self.transform_source(s)
        for attempt in range(self._close_attempts + 1):
            try:
                if self.ignore_extra:
                    return self.raw_decode(s.lstrip())[0]
                return super().decode(s)
            except json.JSONDecodeError as e:
                if e.pos is None:
                    raise
                elif attempt < self._close_attempts:
                    s = self._close_object(e)
                    if s is not None:
                        continue
                raise type(e)(f'{e.msg} in {s[e.pos - 10:e.pos + 10]!r}', s, e.pos)
        assert False, 'Too many attempts to decode JSON'