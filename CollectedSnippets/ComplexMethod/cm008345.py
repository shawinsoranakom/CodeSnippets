def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = None
        if self._get_cookies('https://watch.dropout.tv').get('_session'):
            webpage = self._download_webpage(url, display_id)
        if not webpage or '<div id="watch-unauthorized"' in webpage:
            login_err = self._login(display_id)
            webpage = self._download_webpage(url, display_id)
            if login_err and '<div id="watch-unauthorized"' in webpage:
                if login_err is True:
                    self.raise_login_required(method='any')
                raise ExtractorError(login_err, expected=True)

        embed_url = self._html_search_regex(r'embed_url:\s*["\'](.+?)["\']', webpage, 'embed url')
        thumbnail = self._og_search_thumbnail(webpage)
        watch_info = get_element_by_id('watch-info', webpage) or ''

        title = clean_html(get_element_by_class('video-title', watch_info))
        season_episode = get_element_by_class(
            'site-font-secondary-color', get_element_by_class('text', watch_info))
        episode_number = int_or_none(self._search_regex(
            r'Episode (\d+)', season_episode or '', 'episode', default=None))

        return {
            '_type': 'url_transparent',
            'ie_key': VHXEmbedIE.ie_key(),
            'url': VHXEmbedIE._smuggle_referrer(embed_url, 'https://watch.dropout.tv'),
            'id': self._search_regex(r'embed\.vhx\.tv/videos/(.+?)\?', embed_url, 'id'),
            'display_id': display_id,
            'title': title,
            'description': self._html_search_meta('description', webpage, fatal=False),
            'thumbnail': thumbnail.split('?')[0] if thumbnail else None,  # Ignore crop/downscale
            'series': clean_html(get_element_by_class('series-title', watch_info)),
            'episode_number': episode_number,
            'episode': title if episode_number else None,
            'season_number': int_or_none(self._search_regex(
                r'Season (\d+),', season_episode or '', 'season', default=None)),
            'release_date': unified_strdate(self._search_regex(
                r'data-meta-field-name=["\']release_dates["\'] data-meta-field-value=["\'](.+?)["\']',
                watch_info, 'release date', default=None)),
        }