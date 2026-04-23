def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        event_id = self._search_regex(r"data-id=(['\"])(?P<event_id>\d+)\1", webpage, 'event id', group='event_id')
        event_data = self._download_json(f'https://media.ccc.de/public/events/{event_id}', event_id)

        formats = []
        for recording in event_data.get('recordings', []):
            recording_url = recording.get('recording_url')
            if not recording_url:
                continue
            language = recording.get('language')
            folder = recording.get('folder')
            format_id = None
            if language:
                format_id = language
            if folder:
                if language:
                    format_id += '-' + folder
                else:
                    format_id = folder
            vcodec = 'h264' if 'h264' in folder else (
                'none' if folder in ('mp3', 'opus') else None
            )
            formats.append({
                'format_id': format_id,
                'url': recording_url,
                'width': int_or_none(recording.get('width')),
                'height': int_or_none(recording.get('height')),
                'filesize': int_or_none(recording.get('size'), invscale=1024 * 1024),
                'language': language,
                'vcodec': vcodec,
            })

        return {
            'id': event_id,
            'display_id': display_id,
            'title': event_data['title'],
            'creator': try_get(event_data, lambda x: ', '.join(x['persons'])),
            'description': event_data.get('description'),
            'thumbnail': event_data.get('thumb_url'),
            'timestamp': parse_iso8601(event_data.get('date')),
            'duration': int_or_none(event_data.get('length')),
            'view_count': int_or_none(event_data.get('view_count')),
            'tags': event_data.get('tags'),
            'formats': formats,
        }