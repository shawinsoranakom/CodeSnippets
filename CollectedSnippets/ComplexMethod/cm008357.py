def _entries(self, items, language, type_, **kwargs):
        for item in items:
            video_id = item['id']

            for should_retry in (True, False):
                self._fetch_new_tokens(invalidate=not should_retry)
                try:
                    stream_info = self._download_json(
                        self._proto_relative_url(item['_links']['streams']['href']), video_id, headers={
                            'Accept': 'application/json',
                            'Authorization': f'Bearer {self._access_token}',
                            'Accept-Language': language,
                            'User-Agent': self._USER_AGENT,
                        })
                    break
                except ExtractorError as error:
                    if should_retry and isinstance(error.cause, HTTPError) and error.cause.status == 401:
                        continue
                    raise

            formats = []
            for fmt_url in traverse_obj(stream_info, ('channel', ..., 'stream', ..., 'url', {url_or_none})):
                ext = determine_ext(fmt_url)
                if ext == 'm3u8':
                    fmts = self._extract_m3u8_formats(fmt_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
                    for fmt in fmts:
                        if fmt.get('format_note') and fmt.get('vcodec') == 'none':
                            fmt.update(parse_codecs(fmt['format_note']))
                    formats.extend(fmts)
                elif ext == 'mpd':
                    formats.extend(self._extract_mpd_formats(fmt_url, video_id, mpd_id='dash', fatal=False))
                else:
                    self.report_warning(f'Skipping unsupported format extension "{ext}"')

            yield {
                'id': video_id,
                'title': item.get('title'),
                'composer': item.get('name_composer'),
                'formats': formats,
                'duration': item.get('duration_total'),
                'timestamp': traverse_obj(item, ('date', 'published')),
                'description': item.get('short_description') or stream_info.get('short_description'),
                **kwargs,
                'chapters': [{
                    'start_time': chapter.get('time'),
                    'end_time': try_get(chapter, lambda x: x['time'] + x['duration']),
                    'title': chapter.get('text'),
                } for chapter in item['cuepoints']] if item.get('cuepoints') and type_ == 'concert' else None,
            }