def _real_extract(self, url):
        base_url, show_id, show_title = re.match(self._VALID_URL, url).groups()

        seasons = self._download_info(
            show_id, 'seasons/', show_title)

        show_info = self._download_info(
            show_id, 'info/', show_title, fatal=False)

        if not show_title:
            base_url += "/title"

        entries = []
        for season in (seasons or []):
            episodes = season.get('episodes') or []
            playlist_title = season.get('name') or show_info.get('title')
            for episode in episodes:
                if episode.get('playable') is False:
                    continue
                season_id = str_or_none(episode.get('season_id'))
                video_id = str_or_none(episode.get('video_id'))
                if not (season_id and video_id):
                    continue
                info = self._extract_common_video_info(episode)
                info.update({
                    '_type': 'url_transparent',
                    'ie_key': VVVVIDIE.ie_key(),
                    'url': '/'.join([base_url, season_id, video_id]),
                    'title': episode.get('title'),
                    'description': episode.get('description'),
                    'season_id': season_id,
                    'playlist_title': playlist_title,
                })
                entries.append(info)

        return self.playlist_result(
            entries, show_id, show_info.get('title'), show_info.get('description'))