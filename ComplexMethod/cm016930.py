def _parse_tags(cls, v):
        """
        Accepts a list of strings (possibly multiple form fields),
        where each string can be:
          - JSON array (e.g., '["models","loras","foo"]')
          - comma-separated ('models, loras, foo')
          - single token ('models')
        Returns a normalized, deduplicated, ordered list.
        """
        items: list[str] = []
        if v is None:
            return []
        if isinstance(v, str):
            v = [v]

        if isinstance(v, list):
            for item in v:
                if item is None:
                    continue
                s = str(item).strip()
                if not s:
                    continue
                if s.startswith("["):
                    try:
                        arr = json.loads(s)
                        if isinstance(arr, list):
                            items.extend(str(x) for x in arr)
                            continue
                    except Exception:
                        pass  # fallback to CSV parse below
                items.extend([p for p in s.split(",") if p.strip()])
        else:
            return []

        # normalize + dedupe
        norm = []
        seen = set()
        for t in items:
            tnorm = str(t).strip().lower()
            if tnorm and tnorm not in seen:
                seen.add(tnorm)
                norm.append(tnorm)
        return norm