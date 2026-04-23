def _real_extract(self, url):
        cdn, video_id = self._match_valid_url(url).group('cdn', 'id')
        display_id, video_data = None, None

        if re.match(self._UUID_RE, video_id) or re.match(self._RCS_ID_RE, video_id):
            url = f'https://video.{cdn}/video-json/{video_id}'
        else:
            webpage = self._download_webpage(url, video_id)
            data_config = get_element_html_by_id('divVideoPlayer', webpage) or get_element_html_by_class('divVideoPlayer', webpage)

            if data_config:
                data_config = self._parse_json(
                    extract_attributes(data_config).get('data-config'),
                    video_id, fatal=False) or {}
                if data_config.get('newspaper'):
                    cdn = f'{data_config["newspaper"]}.it'
                display_id, video_id = video_id, data_config.get('uuid') or video_id
                url = f'https://video.{cdn}/video-json/{video_id}'
            else:
                json_url = self._search_regex(
                    r'''(?x)url\s*=\s*(["'])
                    (?P<url>
                        (?:https?:)?//video\.rcs\.it
                        /fragment-includes/video-includes/[^"']+?\.json
                    )\1;''',
                    webpage, video_id, group='url', default=None)
                if json_url:
                    video_data = self._download_json(sanitize_url(json_url, scheme='https'), video_id)
                    display_id, video_id = video_id, video_data.get('id') or video_id

        if not video_data:
            webpage = self._download_webpage(url, video_id)

            video_data = self._search_json(
                '##start-video##', webpage, 'video data', video_id, default=None,
                end_pattern='##end-video##', transform_source=js_to_json)

            if not video_data:
                # try search for iframes
                emb = RCSEmbedsIE._extract_url(webpage)
                if emb:
                    return {
                        '_type': 'url_transparent',
                        'url': emb,
                        'ie_key': RCSEmbedsIE.ie_key(),
                    }

        if not video_data:
            raise ExtractorError('Video data not found in the page')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': video_data.get('title'),
            'description': (clean_html(video_data.get('description'))
                            or clean_html(video_data.get('htmlDescription'))
                            or self._html_search_meta('description', webpage)),
            'uploader': video_data.get('provider') or cdn,
            'formats': list(self._create_formats(self._get_video_src(video_data), video_id)),
        }