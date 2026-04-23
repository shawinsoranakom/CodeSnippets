def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        clip = None

        clip_store = self._parse_json(
            self._html_search_regex(
                r'data-new-clip-store=(["\'])(?P<json>{.+?})\1',
                webpage, 'clip store', default='{}', group='json'),
            video_id, fatal=False)
        if clip_store:
            clips = clip_store.get('clips')
            if clips and isinstance(clips, list) and isinstance(clips[0], dict):
                clip = clips[0]

        def from_clip(field):
            if clip:
                return clip.get(field)

        audio_url = from_clip('clipURLPriorToLoading') or self._og_search_property(
            'audio', webpage, 'audio url')
        title = from_clip('title') or self._html_search_meta(
            ['og:title', 'og:audio:title', 'audio_title'], webpage)
        description = from_clip('description') or clean_html(from_clip('formattedDescription')) or self._og_search_description(webpage)

        duration = float_or_none(from_clip('duration') or self._html_search_meta(
            'weibo:audio:duration', webpage))

        uploader = from_clip('author') or self._html_search_meta(
            ['og:audio:artist', 'twitter:audio:artist_name', 'audio_artist'], webpage, 'uploader')
        uploader_url = from_clip('author_url') or self._html_search_meta(
            'audioboo:channel', webpage, 'uploader url')

        return {
            'id': video_id,
            'url': audio_url,
            'title': title,
            'description': description,
            'duration': duration,
            'uploader': uploader,
            'uploader_url': uploader_url,
        }