def _flatten(self, value):
        # First check if the object is in the object table, not used for
        # containers to ensure that two subcontainers with the same contents
        # will be serialized as distinct values.
        if isinstance(value, _scalars):
            if (type(value), value) in self._objtable:
                return

        elif id(value) in self._objidtable:
            return

        # Add to objectreference map
        refnum = len(self._objlist)
        self._objlist.append(value)
        if isinstance(value, _scalars):
            self._objtable[(type(value), value)] = refnum
        else:
            self._objidtable[id(value)] = refnum

        # And finally recurse into containers
        if isinstance(value, (dict, frozendict)):
            keys = []
            values = []
            items = value.items()
            if self._sort_keys:
                items = sorted(items)

            for k, v in items:
                if not isinstance(k, str):
                    if self._skipkeys:
                        continue
                    raise TypeError("keys must be strings")
                keys.append(k)
                values.append(v)

            for o in itertools.chain(keys, values):
                self._flatten(o)

        elif isinstance(value, (list, tuple)):
            for o in value:
                self._flatten(o)