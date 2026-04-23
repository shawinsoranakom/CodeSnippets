def assert_same_structure(a, b):
    # Fully reimplemented in Python to handle registered classes.

    # Don't handle OrderedDict as a registered class, use the normal dict path
    # so that OrderedDict is equivalent to dict per optree behavior.
    a_registration = REGISTERED_CLASSES.get(type(a), None)
    if type(a) is collections.OrderedDict:
        a_registration = None

    b_registration = REGISTERED_CLASSES.get(type(b), None)
    if type(b) is collections.OrderedDict:
        b_registration = None

    if a_registration != b_registration:
        raise ValueError(
            f"Custom node type mismatch; "
            f"expected type: {type(a)}, got type: {type(b)} "
            f"while comparing {a} and {b}."
        )
    if a_registration is not None:
        a_flat_meta = a_registration.flatten(a)
        b_flat_meta = b_registration.flatten(b)
        a_flat = list(a_flat_meta[0])
        b_flat = list(b_flat_meta[0])
        if not a_flat_meta[1] == b_flat_meta[1]:
            raise ValueError(
                f"Mismatch custom node data; "
                f"expected: {a_flat_meta[1]}, got: {b_flat_meta[1]} "
                f"while comparing {a} and {b}."
            )
        if len(a_flat) != len(b_flat):
            raise ValueError(
                f"Arity mismatch; expected: {len(a)}, got: {len(b)} "
                f"while comparing {a} and {b}."
            )
        for sub_a, sub_b in zip(a_flat, b_flat):
            assert_same_structure(sub_a, sub_b)
    elif not dmtree.is_nested(a):
        if dmtree.is_nested(b):
            raise ValueError(
                f"Structures don't have the same nested structure: {a}, {b}."
            )
    elif isinstance(
        a, (dict, collections.OrderedDict, collections.defaultdict)
    ):
        if not isinstance(
            b, (dict, collections.OrderedDict, collections.defaultdict)
        ):
            raise ValueError(
                f"Expected an instance of dict, collections.OrderedDict, or "
                f"collections.defaultdict, got {type(b)} "
                f"while comparing {a} and {b}."
            )
        a_keys = sorted(a)
        b_keys = sorted(b)
        if not a_keys == b_keys:
            raise ValueError(
                f"Dictionary key mismatch; "
                f"expected key(s): {a_keys}, got key(s): {b_keys} "
                f"while comparing {a} and {b}."
            )
        for key in a_keys:
            assert_same_structure(a[key], b[key])
    elif isinstance(a, collections.abc.Mapping):
        raise ValueError(
            f"Encountered unregistered collections.abc.Mapping type: {type(a)} "
            f"while comparing {a} and {b}."
        )
    else:
        if type(a) is not type(b):
            raise ValueError(
                f"Expected an instance of {type(a)}, got {type(b)} "
                f"while comparing {a} and {b}."
            )
        if not len(a) == len(b):
            raise ValueError(
                f"Arity mismatch; expected: {len(a)}, got: {len(b)} "
                f"while comparing {a} and {b}."
            )
        for sub_a, sub_b in zip(a, b):
            assert_same_structure(sub_a, sub_b)