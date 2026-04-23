def _parse_jwplayer_data(self, jwplayer_data, video_id=None, require_title=True,
                             m3u8_id=None, mpd_id=None, rtmp_params=None, base_url=None):
        entries = []
        if not isinstance(jwplayer_data, dict):
            return entries

        playlist_items = jwplayer_data.get('playlist')
        # JWPlayer backward compatibility: single playlist item/flattened playlists
        # https://github.com/jwplayer/jwplayer/blob/v7.7.0/src/js/playlist/playlist.js#L10
        # https://github.com/jwplayer/jwplayer/blob/v7.4.3/src/js/api/config.js#L81-L96
        if not isinstance(playlist_items, list):
            playlist_items = (playlist_items or jwplayer_data, )

        for video_data in playlist_items:
            if not isinstance(video_data, dict):
                continue
            # JWPlayer backward compatibility: flattened sources
            # https://github.com/jwplayer/jwplayer/blob/v7.4.3/src/js/playlist/item.js#L29-L35
            if 'sources' not in video_data:
                video_data['sources'] = [video_data]

            this_video_id = video_id or video_data['mediaid']

            formats = self._parse_jwplayer_formats(
                video_data['sources'], video_id=this_video_id, m3u8_id=m3u8_id,
                mpd_id=mpd_id, rtmp_params=rtmp_params, base_url=base_url)

            subtitles = {}
            for track in traverse_obj(video_data, (
                    'tracks', lambda _, v: v['kind'].lower() in ('captions', 'subtitles'))):
                track_url = urljoin(base_url, track.get('file'))
                if not track_url:
                    continue
                subtitles.setdefault(track.get('label') or 'en', []).append({
                    'url': self._proto_relative_url(track_url),
                })

            entry = {
                'id': this_video_id,
                'title': unescapeHTML(video_data['title'] if require_title else video_data.get('title')),
                'description': clean_html(video_data.get('description')),
                'thumbnail': urljoin(base_url, self._proto_relative_url(video_data.get('image'))),
                'timestamp': int_or_none(video_data.get('pubdate')),
                'duration': float_or_none(jwplayer_data.get('duration') or video_data.get('duration')),
                'subtitles': subtitles,
                'alt_title': clean_html(video_data.get('subtitle')),  # attributes used e.g. by Tele5 ...
                'genre': clean_html(video_data.get('genre')),
                'channel': clean_html(dict_get(video_data, ('category', 'channel'))),
                'season_number': int_or_none(video_data.get('season')),
                'episode_number': int_or_none(video_data.get('episode')),
                'release_year': int_or_none(video_data.get('releasedate')),
                'age_limit': int_or_none(video_data.get('age_restriction')),
            }
            # https://github.com/jwplayer/jwplayer/blob/master/src/js/utils/validator.js#L32
            if len(formats) == 1 and re.search(r'^(?:http|//).*(?:youtube\.com|youtu\.be)/.+', formats[0]['url']):
                entry.update({
                    '_type': 'url_transparent',
                    'url': formats[0]['url'],
                })
            else:
                entry['formats'] = formats
            entries.append(entry)
        if len(entries) == 1:
            return entries[0]
        else:
            return self.playlist_result(entries)