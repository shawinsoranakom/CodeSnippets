def _real_extract(self, url):
        url, video_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, video_id)

        data = self._parse_json(self._search_regex(
            r'var\s+playlistItem\s*=\s*({.+?});',
            webpage, 'JSON data block'), video_id)

        episode_title = data.get('item_title') or get_element_by_class('episode-title', webpage)
        if not episode_title:
            self._search_regex(
                [r'data-title="([^"]+)"', r'<title>(.+?)</title>'],
                webpage, 'episode title')
        episode_title = episode_title.strip()

        podcast_title = strip_or_none(clean_html(self._search_regex(
            r'<h3>([^<]+)</h3>', webpage, 'podcast title',
            default=None) or get_element_by_class('podcast-title', webpage)))

        title = '%s - %s' % (podcast_title, episode_title) if podcast_title else episode_title

        formats = []
        for k, format_id in (('media_url_libsyn', 'libsyn'), ('media_url', 'main'), ('download_link', 'download')):
            f_url = data.get(k)
            if not f_url:
                continue
            formats.append({
                'url': f_url,
                'format_id': format_id,
            })

        description = self._html_search_regex(
            r'<p\s+id="info_text_body">(.+?)</p>', webpage,
            'description', default=None)
        if description:
            # Strip non-breaking and normal spaces
            description = description.replace('\u00A0', ' ').strip()
        release_date = unified_strdate(self._search_regex(
            r'<div class="release_date">Released: ([^<]+)<',
            webpage, 'release date', default=None) or data.get('release_date'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': data.get('thumbnail_url'),
            'upload_date': release_date,
            'duration': parse_duration(data.get('duration')),
            'formats': formats,
        }