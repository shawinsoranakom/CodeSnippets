def _extract_entries(self, seasons):
        for season in seasons:
            season_id = season.get('id')
            if not season_id:
                continue
            page = 1
            has_more = True
            while has_more is True:
                season = self._download_json(
                    'https://galadriel.puhutv.com/seasons/%s' % season_id,
                    season_id, 'Downloading page %s' % page, query={
                        'page': page,
                        'per': 40,
                    })
                episodes = season.get('episodes')
                if isinstance(episodes, list):
                    for ep in episodes:
                        slug_path = str_or_none(ep.get('slugPath'))
                        if not slug_path:
                            continue
                        video_id = str_or_none(int_or_none(ep.get('id')))
                        yield self.url_result(
                            'https://puhutv.com/%s' % slug_path,
                            ie=PuhuTVIE.ie_key(), video_id=video_id,
                            video_title=ep.get('name') or ep.get('eventLabel'))
                page += 1
                has_more = season.get('hasMore')