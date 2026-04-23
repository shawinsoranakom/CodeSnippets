def to_commands(self, convert_values=lambda vals: vals):
        given = set(self._given)
        result = []
        for id_, vals in self._data.items():
            if isinstance(id_, str) and id_.startswith('virtual_'):
                result.append((Command.CREATE, id_, convert_values(vals)))
                continue
            if id_ not in given:
                result.append(Command.link(id_))
            if vals._changed:
                result.append(Command.update(id_, convert_values(vals)))
        for id_ in self._given:
            if id_ not in self._data:
                result.append(Command.delete(id_))
        return result