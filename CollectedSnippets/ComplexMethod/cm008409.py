def _entries(self, playlist_id, has_episodes, has_articles):
        for i in itertools.count(0) if has_episodes else []:
            page = self._call_lp3(
                'AudioArticle/GetListByCategoryId', {
                    'categoryId': playlist_id,
                    'PageSize': 10,
                    'skip': i,
                    'format': 400,
                }, playlist_id, f'Downloading episode list page {i + 1}')
            if not traverse_obj(page, 'data'):
                break
            for episode in page['data']:
                yield {
                    'id': str(episode['id']),
                    'url': episode['file'],
                    'title': episode.get('title'),
                    'duration': int_or_none(episode.get('duration')),
                    'timestamp': parse_iso8601(episode.get('datePublic')),
                }

        for i in itertools.count(0) if has_articles else []:
            page = self._call_lp3(
                'Article/GetListByCategoryId', {
                    'categoryId': playlist_id,
                    'PageSize': 9,
                    'skip': i,
                    'format': 400,
                }, playlist_id, f'Downloading article list page {i + 1}')
            if not traverse_obj(page, 'data'):
                break
            for article in page['data']:
                yield {
                    '_type': 'url_transparent',
                    'id': str(article['id']),
                    'url': article['url'],
                    'title': article.get('shortTitle'),
                    'description': traverse_obj(article, ('description', 'lead')),
                    'timestamp': parse_iso8601(article.get('datePublic')),
                }