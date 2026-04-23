def _real_extract(self, url):
        video_id, uploader_id = self._match_valid_url(url).group('id', 'uploader_id')
        parsed_url = urllib.parse.urlparse(url)
        base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'

        self._set_cookie(parsed_url.netloc, 'hlsPlayback', 'on')
        full_webpage = webpage = self._download_webpage(url, video_id)

        main_tweet_start = full_webpage.find('class="main-tweet"')
        if main_tweet_start > 0:
            webpage = full_webpage[main_tweet_start:]

        video_url = '{}{}'.format(base_url, self._html_search_regex(
            r'(?:<video[^>]+data-url|<source[^>]+src)="([^"]+)"', webpage, 'video url'))
        ext = determine_ext(video_url)

        if ext == 'unknown_video':
            formats = self._extract_m3u8_formats(video_url, video_id, ext='mp4')
        else:
            formats = [{
                'url': video_url,
                'ext': ext,
            }]

        title = description = self._og_search_description(full_webpage, default=None) or self._html_search_regex(
            r'<div class="tweet-content[^>]+>([^<]+)</div>', webpage, 'title', fatal=False)

        uploader_id = self._html_search_regex(
            r'<a class="username"[^>]+title="@([^"]+)"', webpage, 'uploader id', fatal=False) or uploader_id

        uploader = self._html_search_regex(
            r'<a class="fullname"[^>]+title="([^"]+)"', webpage, 'uploader name', fatal=False)
        if uploader:
            title = f'{uploader} - {title}'

        counts = {
            f'{x[0]}_count': self._html_search_regex(
                fr'<span[^>]+class="icon-{x[1]}[^>]*></span>([^<]*)</div>',
                webpage, f'{x[0]} count', fatal=False)
            for x in (('view', 'play'), ('like', 'heart'), ('repost', 'retweet'), ('comment', 'comment'))
        }
        counts = {field: 0 if count == '' else parse_count(count) for field, count in counts.items()}

        thumbnail = (
            self._html_search_meta('og:image', full_webpage, 'thumbnail url')
            or remove_end('{}{}'.format(base_url, self._html_search_regex(
                r'<video[^>]+poster="([^"]+)"', webpage, 'thumbnail url', fatal=False)), '%3Asmall'))

        thumbnails = [
            {'id': id_, 'url': f'{thumbnail}%3A{id_}'}
            for id_ in ('thumb', 'small', 'large', 'medium', 'orig')
        ]

        date = self._html_search_regex(
            r'<span[^>]+class="tweet-date"[^>]*><a[^>]+title="([^"]+)"',
            webpage, 'upload date', default='').replace('·', '')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'timestamp': unified_timestamp(date),
            'uploader_id': uploader_id,
            'uploader_url': f'{base_url}/{uploader_id}',
            'formats': formats,
            'thumbnails': thumbnails,
            'thumbnail': thumbnail,
            **counts,
        }