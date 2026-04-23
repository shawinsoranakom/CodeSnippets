def _real_extract(self, url):
        video_id = self._match_id(url)

        object_data = self._call_cms(self._get_cms_resource(
            'cms:/objects/' + video_id, video_id), video_id, 'object')['items'][0]
        resource_path = object_data['__links__']['resource']['href']
        video_data = self._call_cms(resource_path, video_id, 'video')
        title = video_data['title']
        description = video_data.get('description')

        if video_data.get('__class__') == 'movie_listing':
            items = self._call_cms(
                video_data['__links__']['movie_listing/movies']['href'],
                video_id, 'movie listing').get('items') or []
            if len(items) != 1:
                entries = []
                for item in items:
                    item_id = item.get('id')
                    if not item_id:
                        continue
                    entries.append(self.url_result(
                        'https://vrv.co/watch/' + item_id,
                        self.ie_key(), item_id, item.get('title')))
                return self.playlist_result(entries, video_id, title, description)
            video_data = items[0]

        streams_path = video_data['__links__'].get('streams', {}).get('href')
        if not streams_path:
            self.raise_login_required()
        streams_json = self._call_cms(streams_path, video_id, 'streams')

        audio_locale = streams_json.get('audio_locale')
        formats = []
        for stream_type, streams in streams_json.get('streams', {}).items():
            if stream_type in ('adaptive_hls', 'adaptive_dash'):
                for stream in streams.values():
                    formats.extend(self._extract_vrv_formats(
                        stream.get('url'), video_id, stream_type.split('_')[1],
                        audio_locale, stream.get('hardsub_locale')))
        self._sort_formats(formats)

        subtitles = {}
        for k in ('captions', 'subtitles'):
            for subtitle in streams_json.get(k, {}).values():
                subtitle_url = subtitle.get('url')
                if not subtitle_url:
                    continue
                subtitles.setdefault(subtitle.get('locale', 'en-US'), []).append({
                    'url': subtitle_url,
                    'ext': subtitle.get('format', 'ass'),
                })

        thumbnails = []
        for thumbnail in video_data.get('images', {}).get('thumbnails', []):
            thumbnail_url = thumbnail.get('source')
            if not thumbnail_url:
                continue
            thumbnails.append({
                'url': thumbnail_url,
                'width': int_or_none(thumbnail.get('width')),
                'height': int_or_none(thumbnail.get('height')),
            })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
            'description': description,
            'duration': float_or_none(video_data.get('duration_ms'), 1000),
            'uploader_id': video_data.get('channel_id'),
            'series': video_data.get('series_title'),
            'season': video_data.get('season_title'),
            'season_number': int_or_none(video_data.get('season_number')),
            'season_id': video_data.get('season_id'),
            'episode': title,
            'episode_number': int_or_none(video_data.get('episode_number')),
            'episode_id': video_data.get('production_episode_id'),
        }