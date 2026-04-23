def _real_extract(self, url):
        content_id = self._match_id(url)
        media = self._download_json(
            f'https://www.rai.tv/dl/RaiTV/programmi/media/ContentItem-{content_id}.html?json',
            content_id, 'Downloading video JSON', fatal=False, expected_status=404)

        if media is None:
            return None

        if 'Audio' in media['type']:
            relinker_info = {
                'formats': [{
                    'format_id': join_nonempty('https', media.get('formatoAudio'), delim='-'),
                    'url': media['audioUrl'],
                    'ext': media.get('formatoAudio'),
                    'vcodec': 'none',
                    'acodec': media.get('formatoAudio'),
                }],
            }
        elif 'Video' in media['type']:
            relinker_info = self._extract_relinker_info(media['mediaUri'], content_id)
        else:
            raise ExtractorError('not a media file')

        thumbnails = self._get_thumbnails_list(
            {image_type: media.get(image_type) for image_type in (
                'image', 'image_medium', 'image_300')}, url)

        return {
            'id': content_id,
            'title': strip_or_none(media.get('name') or media.get('title')),
            'description': strip_or_none(media.get('desc')) or None,
            'thumbnails': thumbnails,
            'uploader': strip_or_none(media.get('author')) or None,
            'upload_date': unified_strdate(media.get('date')),
            'duration': parse_duration(media.get('length')),
            'subtitles': self._extract_subtitles(url, media),
            **relinker_info,
        }