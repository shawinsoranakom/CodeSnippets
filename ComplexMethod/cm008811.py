def apply_path(start_obj, path, test_type):
        objs = (start_obj,)
        has_branched = False

        key = None
        for last, key in lazy_last(variadic(path, (str, bytes, dict, set))):
            if not casesense and isinstance(key, str):
                key = key.casefold()

            if key in (any, all):
                has_branched = False
                filtered_objs = (obj for obj in objs if obj not in (None, {}))
                if key is any:
                    objs = (next(filtered_objs, None),)
                else:
                    objs = (list(filtered_objs),)
                continue

            if key is filter:
                objs = filter(None, objs)
                continue

            if __debug__ and callable(key):
                # Verify function signature
                inspect.signature(key).bind(None, None)

            new_objs = []
            for obj in objs:
                branching, results = apply_key(key, obj, last)
                has_branched |= branching
                new_objs.append(results)

            objs = itertools.chain.from_iterable(new_objs)

        if test_type and not isinstance(key, (dict, list, tuple)):
            objs = map(type_test, objs)

        return objs, has_branched, isinstance(key, dict)