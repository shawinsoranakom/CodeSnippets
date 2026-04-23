def from_dict(
        cls,
        attrs: dict[
            str,
            int
            | float
            | str
            | bool
            | Sequence[int]
            | Sequence[float]
            | Sequence[str]
            | Sequence[bool],
        ],
    ) -> "EncodedAttrs":
        encoded = cls(
            attr_keys=[],
            attr_types=[],
            attr_pos=[],
            attr_ints=[],
            attr_floats=[],
            attr_strs=[],
        )
        for k, v in attrs.items():
            encoded.attr_keys.append(k)
            if isinstance(v, int):
                start_pos = len(encoded.attr_ints)
                encoded.attr_ints.append(v)
                encoded.attr_pos.append((start_pos, start_pos + 1))
                encoded.attr_types.append(_INT_TYPE)
            elif isinstance(v, float):
                start_pos = len(encoded.attr_floats)
                encoded.attr_floats.append(v)
                encoded.attr_pos.append((start_pos, start_pos + 1))
                encoded.attr_types.append(_FLOAT_TYPE)
            elif isinstance(v, str):
                start_pos = len(encoded.attr_strs)
                encoded.attr_strs.append(v)
                encoded.attr_pos.append((start_pos, start_pos + 1))
                encoded.attr_types.append(_STRING_TYPE)
            elif isinstance(v, Sequence):
                if len(v) == 0:
                    raise ValueError(f"Empty sequence for attribute {k}")
                if any(isinstance(elem, float) for elem in v):
                    start_pos = len(encoded.attr_floats)
                    encoded.attr_floats.extend([float(elem) for elem in v])
                    encoded.attr_pos.append((start_pos, start_pos + len(v)))
                    encoded.attr_types.append(_FLOAT_SEQ_TYPE)
                elif isinstance(v[0], int):
                    start_pos = len(encoded.attr_ints)
                    encoded.attr_ints.extend([int(elem) for elem in v])
                    encoded.attr_pos.append((start_pos, start_pos + len(v)))
                    encoded.attr_types.append(_INT_SEQ_TYPE)
                elif isinstance(v[0], str):
                    start_pos = len(encoded.attr_strs)
                    encoded.attr_strs.extend([str(elem) for elem in v])
                    encoded.attr_pos.append((start_pos, start_pos + len(v)))
                    encoded.attr_types.append(_STRING_SEQ_TYPE)
                else:
                    raise ValueError(f"Unsupported sequence type for attribute {k}")
            else:
                raise ValueError(f"Unsupported attribute type for {k}: {type(v)}")
        if len(encoded.attr_keys) != len(encoded.attr_types):
            raise AssertionError(
                f"Mismatch between number of attribute keys and types: {len(encoded.attr_keys)} != {len(encoded.attr_types)}"
            )
        if len(encoded.attr_keys) != len(encoded.attr_pos):
            raise AssertionError(
                f"Mismatch between number of attribute keys and positions: {len(encoded.attr_keys)} != {len(encoded.attr_pos)}"
            )
        return encoded