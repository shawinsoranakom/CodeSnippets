def to_commands(self):
        given = set(self._given)
        result = []
        for id_, vals in self._data.items():
            if isinstance(id_, str) and id_.startswith('virtual_'):
                result.append((Command.CREATE, id_, {
                    key: val.to_commands() if isinstance(val, X2MValue) else val
                    for key, val in vals.changed_items()
                }))
                continue
            if id_ not in given:
                result.append(Command.link(id_))
            if vals._changed:
                result.append(Command.update(id_, {
                    key: val.to_commands() if isinstance(val, X2MValue) else val
                    for key, val in vals.changed_items()
                }))
        for id_ in self._given:
            if id_ not in self._data:
                result.append(Command.unlink(id_))
        return result