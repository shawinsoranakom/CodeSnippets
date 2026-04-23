def _entries(self, playlist_id, canonical_id, season_numbers, requested_season_number):
        for season_idx, season_number in enumerate(season_numbers):
            if requested_season_number is not None and requested_season_number != season_number:
                continue

            cursor = None
            for page_number in itertools.count(1):
                page = self._fetch_page(
                    playlist_id, canonical_id, season_idx, season_number, page_number, cursor)

                nodes = traverse_obj(page, ('seasons', 'nodes', ...))

                for episode in traverse_obj(nodes, (
                    ..., 'episodes', 'nodes', lambda _, v: url_or_none(v['sharingUrl']),
                )):
                    yield self.url_result(
                        episode['sharingUrl'], ZDFIE,
                        **traverse_obj(episode, {
                            'id': ('canonical', {str}),
                            'title': ('teaser', 'title', {str}),
                            'description': (('leadParagraph', ('teaser', 'description')), any, {str}),
                            'timestamp': ('editorialDate', {parse_iso8601}),
                            'episode_number': ('episodeInfo', 'episodeNumber', {int_or_none}),
                            'season_number': ('episodeInfo', 'seasonNumber', {int_or_none}),
                        }))

                page_info = traverse_obj(nodes, (-1, 'episodes', 'pageInfo', {dict})) or {}
                if not page_info.get('hasNextPage') or not page_info.get('endCursor'):
                    break
                cursor = page_info['endCursor']