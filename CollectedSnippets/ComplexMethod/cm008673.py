def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'slug')
        _is_article = video_id is None
        webpage = self._download_webpage(url, video_id or display_id)
        if _is_article:
            video_id = self._search_regex(
                r'<article[^>]*\sid=["\']Article_(\d+)["\']', webpage, 'article id')
        player_attrs = self._extract_player_attrs(webpage)
        title = player_attrs.get('label') or self._og_search_title(webpage)
        description = get_element_by_class(
            'article-wrapper' if _is_article else 'story_content',
            webpage)
        description = clean_html(re.sub(r'<script[^>]*>[^<]+</script>', '', description))
        if not description:
            description = self._og_search_description(webpage)
        thumbnail = player_attrs.get('image') or self._og_search_thumbnail(webpage)
        timestamp = unified_timestamp(self._html_search_meta(
            'article:published_time', webpage))
        source = player_attrs.get('source')
        if not source:
            raise ExtractorError('No source found', video_id=video_id)
        if determine_ext(source) == 'm3u8':
            formats, subs = self._extract_m3u8_formats_and_subtitles(source, video_id, 'mp4')
        else:
            formats, subs = [{'url': source}], {}
        if player_attrs.get('subs'):
            self._merge_subtitles({'und': [{'url': player_attrs['subs']}]}, target=subs)
        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'formats': formats,
            'subtitles': subs,
        }