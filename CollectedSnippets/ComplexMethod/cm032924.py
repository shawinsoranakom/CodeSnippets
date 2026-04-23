def _search_with_search_after(self, index_names: list[str], query: dict, offset: int, limit: int):
        q_base = copy.deepcopy(query)
        q_base.pop("from", None)
        q_base.pop("size", None)

        search_after = None
        template_res = None
        collected_hits = []
        remaining_skip = max(0, offset)
        remaining_take = max(0, limit)
        with_aggs = True

        while remaining_skip > 0:
            batch = min(SEARCH_AFTER_BATCH_SIZE, remaining_skip)
            q_iter = copy.deepcopy(q_base)
            q_iter["size"] = batch
            if search_after is not None:
                q_iter["search_after"] = search_after
            if not with_aggs:
                q_iter.pop("aggs", None)
            res = self._es_search_once(index_names, q_iter, track_total_hits=template_res is None)
            if template_res is None:
                template_res = res
            hits = res.get("hits", {}).get("hits", [])
            if not hits:
                break
            next_search_after = hits[-1].get("sort")
            if not next_search_after or next_search_after == search_after:
                break
            search_after = next_search_after
            remaining_skip -= len(hits)
            with_aggs = False
            if len(hits) < batch:
                break

        while remaining_skip <= 0 and remaining_take > 0:
            batch = min(SEARCH_AFTER_BATCH_SIZE, remaining_take)
            q_iter = copy.deepcopy(q_base)
            q_iter["size"] = batch
            if search_after is not None:
                q_iter["search_after"] = search_after
            if not with_aggs:
                q_iter.pop("aggs", None)
            res = self._es_search_once(index_names, q_iter, track_total_hits=template_res is None)
            if template_res is None:
                template_res = res
            hits = res.get("hits", {}).get("hits", [])
            if not hits:
                break
            collected_hits.extend(hits)
            remaining_take -= len(hits)
            next_search_after = hits[-1].get("sort")
            if not next_search_after or next_search_after == search_after:
                break
            search_after = next_search_after
            with_aggs = False
            if len(hits) < batch:
                break

        if template_res is None:
            q_count = copy.deepcopy(q_base)
            q_count["size"] = 0
            template_res = self._es_search_once(index_names, q_count, track_total_hits=True)
        template_res["hits"]["hits"] = collected_hits
        return template_res