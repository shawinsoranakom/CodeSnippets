def propagate_frozenset(unordered_import_structure):
        frozenset_first_import_structure = {}
        for _key, _value in unordered_import_structure.items():
            # If the value is not a dict but a string, no need for custom manipulation
            if not isinstance(_value, dict):
                frozenset_first_import_structure[_key] = _value

            elif any(isinstance(v, frozenset) for v in _value):
                for k, v in _value.items():
                    if isinstance(k, frozenset):
                        # Here we want to switch around _key and k to propagate k upstream if it is a frozenset
                        if k not in frozenset_first_import_structure:
                            frozenset_first_import_structure[k] = {}
                        if _key not in frozenset_first_import_structure[k]:
                            frozenset_first_import_structure[k][_key] = {}

                        frozenset_first_import_structure[k][_key].update(v)

                    else:
                        # If k is not a frozenset, it means that the dictionary is not "level": some keys (top-level)
                        # are frozensets, whereas some are not -> frozenset keys are at an unknown depth-level of the
                        # dictionary.
                        #
                        # We recursively propagate the frozenset for this specific dictionary so that the frozensets
                        # are at the top-level when we handle them.
                        propagated_frozenset = propagate_frozenset({k: v})
                        for r_k, r_v in propagated_frozenset.items():
                            if isinstance(_key, frozenset):
                                if r_k not in frozenset_first_import_structure:
                                    frozenset_first_import_structure[r_k] = {}
                                if _key not in frozenset_first_import_structure[r_k]:
                                    frozenset_first_import_structure[r_k][_key] = {}

                                # _key is a frozenset -> we switch around the r_k and _key
                                frozenset_first_import_structure[r_k][_key].update(r_v)
                            else:
                                if _key not in frozenset_first_import_structure:
                                    frozenset_first_import_structure[_key] = {}
                                if r_k not in frozenset_first_import_structure[_key]:
                                    frozenset_first_import_structure[_key][r_k] = {}

                                # _key is not a frozenset -> we keep the order of r_k and _key
                                frozenset_first_import_structure[_key][r_k].update(r_v)

            else:
                frozenset_first_import_structure[_key] = propagate_frozenset(_value)

        return frozenset_first_import_structure