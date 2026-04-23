def _traverse_obj(obj, path, allow_empty, test_type):
        results, has_branched, is_dict = apply_path(obj, path, test_type)
        results = LazyList(x for x in results if x not in (None, {}))

        if get_all and has_branched:
            if results:
                return results.exhaust()
            if allow_empty:
                return [] if default is NO_DEFAULT else default
            return None

        return results[0] if results else {} if allow_empty and is_dict else None