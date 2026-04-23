def decode_rows(self, stream, conversors):
        for row in stream:
            values = _parse_values(row)

            if isinstance(values, dict):
                if values and max(values) >= len(conversors):
                    raise BadDataFormat(row)
                # XXX: int 0 is used for implicit values, not '0'
                values = [values[i] if i in values else 0 for i in
                          range(len(conversors))]
            else:
                if len(values) != len(conversors):
                    raise BadDataFormat(row)

            yield self._decode_values(values, conversors)