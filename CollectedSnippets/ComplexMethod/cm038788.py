def recursive_dict_update(
            original: dict[str, Any],
            update: dict[str, Any],
        ) -> set[str]:
            """Recursively updates a dictionary with another dictionary.
            Returns a set of duplicate keys that were overwritten.
            """
            duplicates = set[str]()
            for k, v in update.items():
                if isinstance(v, dict) and isinstance(original.get(k), dict):
                    nested_duplicates = recursive_dict_update(original[k], v)
                    duplicates |= {f"{k}.{d}" for d in nested_duplicates}
                elif isinstance(v, list) and isinstance(original.get(k), list):
                    original[k] += v
                else:
                    if k in original:
                        duplicates.add(k)
                    original[k] = v
            return duplicates