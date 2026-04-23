def create_name(self, candidate: str, obj: object | None) -> str:
        """Create a unique name.

        Arguments:
            candidate: used as the basis for the unique name, relevant to the user.
            obj: If not None, an object that will be associated with the unique name.
        """
        if obj is not None and obj in self._obj_to_name:
            return self._obj_to_name[obj]

        # optimistically check if candidate is already a valid name
        match = _name_regex.match(candidate)
        if match is None:
            # delete all characters that are illegal in a Python identifier
            candidate = _illegal_char_regex.sub("_", candidate)

            if not candidate:
                candidate = "_unnamed"

            if candidate[0].isdigit():
                candidate = f"_{candidate}"

            match = _name_regex.match(candidate)
            if match is None:
                raise AssertionError(
                    f"Name regex failed to match candidate: {candidate}"
                )

        base, num = match.group(1, 2)
        if num is None or candidate in self._used_names:
            # Look up `base` to match the key used in the store on line below;
            # using `candidate` misses when it has a numeric suffix, making
            # the while-loop quadratic.
            num = self._base_count.get(base, 0)
            if _illegal_names.get(candidate, obj) is not obj:
                num += 1
                candidate = f"{base}_{num}"
                # assume illegal names don't end in _\d so no need to check again
        else:
            num = int(num)

        while candidate in self._used_names:
            num += 1
            candidate = f"{base}_{num}"

        self._used_names.add(candidate)
        self._base_count[base] = num
        if obj is not None:
            self._obj_to_name[obj] = candidate
        return candidate