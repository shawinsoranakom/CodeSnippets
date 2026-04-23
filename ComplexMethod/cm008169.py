def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(f'https://audioboom.com/posts/{video_id}', video_id)

        clip_store = self._search_json(
            r'data-react-class="V5DetailPagePlayer"\s*data-react-props=["\']',
            webpage, 'clip store', video_id, fatal=False, transform_source=unescapeHTML)
        clip = traverse_obj(clip_store, ('clips', 0), expected_type=dict) or {}

        return {
            'id': video_id,
            'url': clip.get('clipURLPriorToLoading') or self._og_search_property('audio', webpage, 'audio url'),
            'title': clip.get('title') or self._html_search_meta(['og:title', 'og:audio:title', 'audio_title'], webpage),
            'description': (clip.get('description') or clean_html(clip.get('formattedDescription'))
                            or self._og_search_description(webpage)),
            'duration': float_or_none(clip.get('duration') or self._html_search_meta('weibo:audio:duration', webpage)),
            'uploader': clip.get('author') or self._html_search_meta(
                ['og:audio:artist', 'twitter:audio:artist_name', 'audio_artist'], webpage, 'uploader'),
            'uploader_url': clip.get('author_url') or self._html_search_regex(
                r'<div class="avatar flex-shrink-0">\s*<a href="(?P<uploader_url>http[^"]+)"',
                webpage, 'uploader url', fatal=False),
        }