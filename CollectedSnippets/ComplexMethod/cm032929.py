def get_fields(self, res, fields: list[str]) -> dict[str, dict]:
        res_fields = {}
        if not fields:
            return {}
        hits = res.get("hits", {}).get("hits", [])
        for hit in hits:
            doc_id = hit.get("_id")
            d = hit.get("_source", {})
            # Also extract fields from ES "fields" response (used by dense_vector in ES 9.x)
            hit_fields = hit.get("fields", {})
            m = {}
            for n in fields:
                # First check _source
                if d.get(n) is not None:
                    m[n] = d.get(n)
                # Then check fields (ES 9.x stores dense_vector here, not in _source)
                elif n in hit_fields:
                    vals = hit_fields[n]
                    # ES fields response wraps dense_vector in 2 levels: [[v1,v2,...]] -> [v1,v2,...]
                    if isinstance(vals, list) and len(vals) == 1:
                        vals = vals[0]
                    m[n] = vals
            for n, v in m.items():
                if isinstance(v, list):
                    m[n] = v
                    continue
                if n == "available_int" and isinstance(v, (int, float)):
                    m[n] = v
                    continue
                if not isinstance(v, str):
                    m[n] = str(m[n])
                # if n.find("tks") > 0:
                #     m[n] = remove_redundant_spaces(m[n])

            if m:
                res_fields[doc_id] = m
        return res_fields