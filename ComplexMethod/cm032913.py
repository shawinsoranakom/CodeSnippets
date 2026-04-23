def get_aggregation(self, res, fieldnm: str):
        if len(res.chunks) == 0:
            return []

        counts = {}
        result = []
        for d in res.chunks:
            if "value" in d and "count" in d:
                # directly use the aggregation result
                result.append((d["value"], d["count"]))
            elif fieldnm in d:
                # aggregate the values of specific field
                v = d[fieldnm]
                if isinstance(v, list):
                    for vv in v:
                        if isinstance(vv, str) and vv.strip():
                            counts[vv] = counts.get(vv, 0) + 1
                elif isinstance(v, str) and v.strip():
                    counts[v] = counts.get(v, 0) + 1

        if len(counts) > 0:
            for k, v in counts.items():
                result.append((k, v))

        return result