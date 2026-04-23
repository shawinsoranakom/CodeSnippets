def get_variable_param_value(self, obj: Any, path: str) -> Any:
        cur = obj
        if not path:
            return cur
        for key in path.split('.'):
            if cur is None:
                return None

            if isinstance(cur, str):
                try:
                    cur = json.loads(cur)
                except Exception:
                    return None

            if isinstance(cur, dict):
                cur = cur.get(key)
                continue

            if isinstance(cur, (list, tuple)):
                try:
                    idx = int(key)
                    cur = cur[idx]
                except Exception:
                    return None
                continue

            cur = getattr(cur, key, None)
        return cur