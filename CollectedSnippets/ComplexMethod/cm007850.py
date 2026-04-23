def _extract_video(self, video_id, webpage, fatal=False):

        data = self._download_json(
            'http://bits.orf.at/filehandler/static-api/json/current/data.json?file=%s' % video_id,
            video_id)[0]

        video = traverse_obj(data, (
            'sources', ('default', 'q8c'),
            T(lambda x: x if x['loadBalancerUrl'] else None),
            any))

        load_balancer_url = video['loadBalancerUrl']

        try:
            rendition = self._download_json(
                load_balancer_url, video_id, transform_source=strip_jsonp)
        except ExtractorError:
            rendition = None

        if not rendition:
            rendition = {
                'redirect': {
                    'smil': re.sub(
                        r'(/)jsonp(/.+\.)mp4$', r'\1dash\2smil/manifest.mpd',
                        load_balancer_url),
                },
            }

        f = traverse_obj(video, {
            'abr': ('audioBitrate', T(int_or_none)),
            'vbr': ('bitrate', T(int_or_none)),
            'fps': ('videoFps', T(int_or_none)),
            'width': ('videoWidth', T(int_or_none)),
            'height': ('videoHeight', T(int_or_none)),
        })

        formats = []
        for format_id, format_url in traverse_obj(rendition, (
                'redirect', T(dict.items), Ellipsis)):
            if format_id == 'rtmp':
                ff = f.copy()
                ff.update({
                    'url': format_url,
                    'format_id': format_id,
                })
                formats.append(ff)
            elif determine_ext(format_url) == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    format_url, video_id, f4m_id=format_id))
            elif determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', m3u8_id=format_id,
                    entry_protocol='m3u8_native'))
            elif determine_ext(format_url) == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id=format_id))

        if formats or fatal:
            self._sort_formats(formats)
        else:
            return

        return merge_dicts({
            'id': video_id,
            'title': re.sub(self._TITLE_STRIP_RE, '', self._og_search_title(webpage)),
            'description': self._og_search_description(webpage),
            'upload_date': unified_strdate(self._html_search_meta(
                'dc.date', webpage, 'upload date', fatal=False)),
            'formats': formats,
        }, traverse_obj(data, {
            'duration': ('duration', T(k_float_or_none)),
            'thumbnail': ('sources', 'default', 'preview', T(url_or_none)),
        }), rev=True)