def _extract_from_id(self, video_id, webpage=None):
        response = self._download_json(
            'http://qi.ckm.onetapi.pl/', video_id,
            query={
                'body[id]': video_id,
                'body[jsonrpc]': '2.0',
                'body[method]': 'get_asset_detail',
                'body[params][ID_Publikacji]': video_id,
                'body[params][Service]': 'www.onet.pl',
                'content-type': 'application/jsonp',
                'x-onet-app': 'player.front.onetapi.pl',
            })

        error = response.get('error')
        if error:
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, error['message']), expected=True)

        video = response['result'].get('0')

        formats = []
        for format_type, formats_dict in video['formats'].items():
            if not isinstance(formats_dict, dict):
                continue
            for format_id, format_list in formats_dict.items():
                if not isinstance(format_list, list):
                    continue
                for f in format_list:
                    video_url = f.get('url')
                    if not video_url:
                        continue
                    ext = determine_ext(video_url)
                    if format_id.startswith('ism'):
                        formats.extend(self._extract_ism_formats(
                            video_url, video_id, 'mss', fatal=False))
                    elif ext == 'mpd':
                        formats.extend(self._extract_mpd_formats(
                            video_url, video_id, mpd_id='dash', fatal=False))
                    elif format_id.startswith('hls'):
                        formats.extend(self._extract_m3u8_formats(
                            video_url, video_id, 'mp4', 'm3u8_native',
                            m3u8_id='hls', fatal=False))
                    else:
                        http_f = {
                            'url': video_url,
                            'format_id': format_id,
                            'abr': float_or_none(f.get('audio_bitrate')),
                        }
                        if format_type == 'audio':
                            http_f['vcodec'] = 'none'
                        else:
                            http_f.update({
                                'height': int_or_none(f.get('vertical_resolution')),
                                'width': int_or_none(f.get('horizontal_resolution')),
                                'vbr': float_or_none(f.get('video_bitrate')),
                            })
                        formats.append(http_f)
        self._sort_formats(formats)

        meta = video.get('meta', {})

        title = (self._og_search_title(
            webpage, default=None) if webpage else None) or meta['title']
        description = (self._og_search_description(
            webpage, default=None) if webpage else None) or meta.get('description')
        duration = meta.get('length') or meta.get('lenght')
        timestamp = parse_iso8601(meta.get('addDate'), ' ')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'timestamp': timestamp,
            'formats': formats,
        }