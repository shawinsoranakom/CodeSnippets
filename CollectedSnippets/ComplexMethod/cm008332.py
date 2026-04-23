def _real_extract(self, url):
        mobj = self._match_valid_url(url).groupdict()
        info_slug = mobj['series_or_movie_slug']
        video_json = self._download_json(self._INFO_URL + info_slug, info_slug, query=self._INFO_QUERY_PARAMS)

        if mobj['video_type'] == 'series':
            series_name = video_json.get('name', info_slug)
            season_number, episode_slug = mobj.get('season_number'), mobj.get('episode_slug')

            videos = []
            for season in video_json['seasons']:
                if season_number is not None and season_number != int_or_none(season.get('number')):
                    continue
                for episode in season['episodes']:
                    if episode_slug is not None and episode_slug != episode.get('slug'):
                        continue
                    videos.append(self._get_video_info(episode, episode_slug, series_name))
            if not videos:
                raise ExtractorError('Failed to find any videos to extract')
            if episode_slug is not None and len(videos) == 1:
                return videos[0]
            playlist_title = series_name
            if season_number is not None:
                playlist_title += ' - Season %d' % season_number
            return self.playlist_result(videos,
                                        playlist_id=video_json.get('_id', info_slug),
                                        playlist_title=playlist_title)
        return self._get_video_info(video_json, info_slug)