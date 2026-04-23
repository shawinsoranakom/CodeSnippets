def _get_text(data, *path_list, max_runs=None):
        for path in path_list or [None]:
            if path is None:
                obj = [data]
            else:
                obj = traverse_obj(data, path, default=[])
                if not any(key is ... or isinstance(key, (list, tuple)) for key in variadic(path)):
                    obj = [obj]
            for item in obj:
                text = try_get(item, lambda x: x['simpleText'], str)
                if text:
                    return text
                runs = try_get(item, lambda x: x['runs'], list) or []
                if not runs and isinstance(item, list):
                    runs = item

                runs = runs[:min(len(runs), max_runs or len(runs))]
                text = ''.join(traverse_obj(runs, (..., 'text'), expected_type=str))
                if text:
                    return text