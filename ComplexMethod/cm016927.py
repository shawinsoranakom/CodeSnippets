def _split_csv_tags(cls, v):
        # Accept "a,b,c" or ["a","b"] (we are liberal in what we accept)
        if v is None:
            return []
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        if isinstance(v, list):
            out: list[str] = []
            for item in v:
                if isinstance(item, str):
                    out.extend([t.strip() for t in item.split(",") if t.strip()])
            return out
        return v