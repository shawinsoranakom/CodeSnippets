def _entries(self, show_id):
        for page_num in itertools.count(1):
            episodes = self._download_json(
                'https://api.spreaker.com/show/%s/episodes' % show_id,
                show_id, note='Downloading JSON page %d' % page_num, query={
                    'page': page_num,
                    'max_per_page': 100,
                })
            pager = try_get(episodes, lambda x: x['response']['pager'], dict)
            if not pager:
                break
            results = pager.get('results')
            if not results or not isinstance(results, list):
                break
            for result in results:
                if not isinstance(result, dict):
                    continue
                yield _extract_episode(result)
            if page_num == pager.get('last_page'):
                break