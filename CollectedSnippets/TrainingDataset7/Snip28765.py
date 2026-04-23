def _map_related_query_names(self, res):
        return tuple((o.name, m) for o, m in res)