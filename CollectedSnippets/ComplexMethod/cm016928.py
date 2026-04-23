def _normalize_tags_field(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            out = [str(t).strip().lower() for t in v if str(t).strip()]
            seen = set()
            dedup = []
            for t in out:
                if t not in seen:
                    seen.add(t)
                    dedup.append(t)
            return dedup
        if isinstance(v, str):
            return [t.strip().lower() for t in v.split(",") if t.strip()]
        return []