def _extract_api_data(self, video, video_id):
        if video.get('error_code') == 'contentGeoblocked':
            self.raise_geo_restricted(countries=video['geo_locations'])

        formats, subs = [], {}
        for format_id, format_url in video['source'].items():
            ext = determine_ext(format_url)
            if ext == 'm3u8':
                formats_, subs_ = self._extract_m3u8_formats_and_subtitles(
                    format_url, video_id, 'mp4', m3u8_id=format_id,
                    fatal=False)
                formats.extend(formats_)
                self._merge_subtitles(subs_, target=subs)
            else:
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                })
        if video.get('language'):
            for fmt in formats:
                fmt['language'] = video['language']

        images = (video.get('images') or []) + [video.get('image') or {}]
        thumbnails = [{
            'id': image.get('id'),
            'url': f'{image["url"]}/profile:player-960x540',
            'width': 960,
            'height': 540,
        } for image in images if image.get('url')]
        self._remove_duplicate_formats(thumbnails)

        return {
            'id': video.get('clip_id') or video_id,
            'title': video.get('title'),
            'description': video.get('description'),
            'thumbnails': thumbnails,
            'duration': int_or_none(video.get('clip_duration')),
            'timestamp': video.get('created_at'),
            'formats': formats,
            'subtitles': subs,
        }