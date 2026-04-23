def _extract_series(self, video_id, season_titles=None, season_numbers=None):
        media_info = self._call_api(video_id, method='Tile/GetSeriesDetails', id=video_id)

        series = try_get(media_info, lambda x: x['Series'], dict) or {}
        series_info = {
            'age_limit': self._parse_age_rating(series),
            'title': series.get('Title'),
            'description': dict_get(series, ('ShortDescription', 'TinyDescription')),
        }
        if season_numbers:
            season_titles = season_titles or []
            for season in try_get(series, lambda x: x['Seasons'], list) or []:
                if season.get('SeasonNumber') in season_numbers and season.get('Title'):
                    season_titles.append(season['Title'])

        def gen_episode(m_info, season_titles):
            for episode_group in try_get(m_info, lambda x: x['EpisodeGroups'], list) or []:
                if season_titles and episode_group.get('Title') not in season_titles:
                    continue
                episodes = try_get(episode_group, lambda x: x['Episodes'], list)
                if not episodes:
                    continue
                season_info = {
                    'season': episode_group.get('Title'),
                    'season_number': int_or_none(episode_group.get('SeasonNumber')),
                }
                try:
                    episodes = [(int(ep['EpisodeNumber']), ep) for ep in episodes]
                    episodes.sort()
                except (KeyError, ValueError):
                    episodes = enumerate(episodes, 1)
                for n, episode in episodes:
                    info = self._extract_episode(episode)
                    if info is None:
                        continue
                    info['episode_number'] = n
                    info.update(season_info)
                    yield info

        return self.playlist_result(
            gen_episode(media_info, season_titles), playlist_id=video_id, **series_info)