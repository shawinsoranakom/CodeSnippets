def _real_extract(self, url):
        domain, video_id = self._match_valid_url(url).group('domain', 'id')
        webpage = self._download_webpage(url, video_id)
        initial_data = traverse_obj(
            self._search_nextjs_data(webpage, video_id, fatal=False), ('props', 'pageProps', 'initialContentData'), default={})

        try:
            stream_data = self._download_json(
                f'https://{domain}/cmsPostProxy/contents/video/{video_id}/streamer?os=android', video_id, data=b'')['data']
        except ExtractorError as e:
            if not isinstance(e.cause, HTTPError):
                raise e
            errmsg = self._parse_json(e.cause.response.read().decode(), video_id)['meta']['message']
            if 'country' in errmsg:
                self.raise_geo_restricted(
                    errmsg, [initial_data['display_country']] if initial_data.get('display_country') else None, True)
            else:
                self.raise_no_formats(errmsg, video_id=video_id)

        if stream_data:
            stream_url = stream_data['stream']['stream_url']
            stream_ext = determine_ext(stream_url)
            if stream_ext == 'm3u8':
                formats, subs = self._extract_m3u8_formats_and_subtitles(stream_url, video_id, 'mp4')
            elif stream_ext == 'mpd':
                formats, subs = self._extract_mpd_formats_and_subtitles(stream_url, video_id)
            else:
                formats = [{'url': stream_url}]

        thumbnails = [
            {'id': thumb_key, 'url': thumb_url}
            for thumb_key, thumb_url in (initial_data.get('thumb_list') or {}).items()
            if url_or_none(thumb_url)]

        return {
            'id': video_id,
            'title': initial_data.get('title') or self._html_search_regex(
                [r'Nonton (?P<name>.+) Gratis',
                 r'Xem (?P<name>.+) Miễn phí',
                 r'Watch (?P<name>.+) Free'], webpage, 'title', group='name'),
            'display_id': initial_data.get('slug_title'),
            'description': initial_data.get('synopsis'),
            'timestamp': unified_timestamp(initial_data.get('create_date')),
            # 'duration': int_or_none(initial_data.get('duration'), invscale=60),  # duration field must atleast be accurate to the second
            'categories': traverse_obj(initial_data, ('article_category_details', ..., 'name')),
            'release_timestamp': unified_timestamp(initial_data.get('publish_date')),
            'release_year': int_or_none(initial_data.get('release_year')),
            'formats': formats,
            'subtitles': subs,
            'thumbnails': thumbnails,
            'age_limit': self._CUSTOM_RATINGS.get(initial_data.get('rate')) or parse_age_limit(initial_data.get('rate')),
            'cast': traverse_obj(initial_data, (('actor', 'director'), ...)),
            'view_count': int_or_none(initial_data.get('count_views')),
            'like_count': int_or_none(initial_data.get('count_likes')),
            'average_rating': int_or_none(initial_data.get('count_ratings')),
        }