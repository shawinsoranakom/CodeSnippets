def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_urls = re.findall(
            r'<video[^>]+><source[^>]+src=["\'](.+?)["\']', webpage)

        iframe_links = re.findall(
            r'<iframe[^>]+src=["\']((?:https?:)?//embed\.life\.ru/(?:embed|video)/.+?)["\']',
            webpage)

        if not video_urls and not iframe_links:
            raise ExtractorError(f'No media links available for {video_id}')

        title = remove_end(
            self._og_search_title(webpage),
            ' - Life.ru')

        description = self._og_search_description(webpage)

        view_count = self._html_search_regex(
            r'<div[^>]+class=(["\']).*?\bhits-count\b.*?\1[^>]*>\s*(?P<value>\d+)\s*</div>',
            webpage, 'view count', fatal=False, group='value')

        timestamp = parse_iso8601(self._search_regex(
            r'<time[^>]+datetime=(["\'])(?P<value>.+?)\1',
            webpage, 'upload date', fatal=False, group='value'))

        common_info = {
            'description': description,
            'view_count': int_or_none(view_count),
            'timestamp': timestamp,
        }

        def make_entry(video_id, video_url, index=None):
            cur_info = dict(common_info)
            cur_info.update({
                'id': video_id if not index else f'{video_id}-video{index}',
                'url': video_url,
                'title': title if not index else f'{title} (Видео {index})',
            })
            return cur_info

        def make_video_entry(video_id, video_url, index=None):
            video_url = urllib.parse.urljoin(url, video_url)
            return make_entry(video_id, video_url, index)

        def make_iframe_entry(video_id, video_url, index=None):
            video_url = self._proto_relative_url(video_url, 'http:')
            cur_info = make_entry(video_id, video_url, index)
            cur_info['_type'] = 'url_transparent'
            return cur_info

        if len(video_urls) == 1 and not iframe_links:
            return make_video_entry(video_id, video_urls[0])

        if len(iframe_links) == 1 and not video_urls:
            return make_iframe_entry(video_id, iframe_links[0])

        entries = []

        if video_urls:
            for num, video_url in enumerate(video_urls, 1):
                entries.append(make_video_entry(video_id, video_url, num))

        if iframe_links:
            for num, iframe_link in enumerate(iframe_links, len(video_urls) + 1):
                entries.append(make_iframe_entry(video_id, iframe_link, num))

        playlist = common_info.copy()
        playlist.update(self.playlist_result(entries, video_id, title, description))
        return playlist