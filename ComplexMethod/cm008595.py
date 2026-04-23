def _real_extract(self, url):
        live, media_id = self._match_valid_url(url).groups()
        embed_page = self._download_webpage(
            'https://www.rtbf.be/auvio/embed/' + ('direct' if live else 'media'),
            media_id, query={'id': media_id})

        media_data = self._html_search_regex(r'data-media="([^"]+)"', embed_page, 'media data', fatal=False)
        if not media_data:
            if re.search(r'<div[^>]+id="js-error-expired"[^>]+class="(?![^"]*hidden)', embed_page):
                raise ExtractorError('Livestream has ended.', expected=True)
            if re.search(r'<div[^>]+id="js-sso-connect"[^>]+class="(?![^"]*hidden)', embed_page):
                self.raise_login_required()

            raise ExtractorError('Could not find media data')

        data = self._parse_json(media_data, media_id)

        error = data.get('error')
        if error:
            raise ExtractorError(f'{self.IE_NAME} said: {error}', expected=True)

        provider = data.get('provider')
        if provider in self._PROVIDERS:
            return self.url_result(data['url'], self._PROVIDERS[provider])

        title = traverse_obj(data, 'subtitle', 'title')
        is_live = data.get('isLive')
        height_re = r'-(\d+)p\.'
        formats, subtitles = [], {}

        # The old api still returns m3u8 and mpd manifest for livestreams, but these are 'fake'
        # since all they contain is a 20s video that is completely unrelated.
        # https://github.com/yt-dlp/yt-dlp/issues/4656#issuecomment-1214461092
        m3u8_url = None if data.get('isLive') else traverse_obj(data, 'urlHlsAes128', 'urlHls')
        if m3u8_url:
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, media_id, 'mp4', m3u8_id='hls', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        fix_url = lambda x: x.replace('//rtbf-vod.', '//rtbf.') if '/geo/drm/' in x else x
        http_url = data.get('url')
        if formats and http_url and re.search(height_re, http_url):
            http_url = fix_url(http_url)
            for m3u8_f in formats[:]:
                height = m3u8_f.get('height')
                if not height:
                    continue
                f = m3u8_f.copy()
                del f['protocol']
                f.update({
                    'format_id': m3u8_f['format_id'].replace('hls-', 'http-'),
                    'url': re.sub(height_re, '-%dp.' % height, http_url),
                })
                formats.append(f)
        else:
            sources = data.get('sources') or {}
            for key, format_id in self._QUALITIES:
                format_url = sources.get(key)
                if not format_url:
                    continue
                height = int_or_none(self._search_regex(
                    height_re, format_url, 'height', default=None))
                formats.append({
                    'format_id': format_id,
                    'url': fix_url(format_url),
                    'height': height,
                })

        mpd_url = None if data.get('isLive') else data.get('urlDash')
        if mpd_url and (self.get_param('allow_unplayable_formats') or not data.get('drm')):
            fmts, subs = self._extract_mpd_formats_and_subtitles(
                mpd_url, media_id, mpd_id='dash', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        audio_url = data.get('urlAudio')
        if audio_url:
            formats.append({
                'format_id': 'audio',
                'url': audio_url,
                'vcodec': 'none',
            })

        for track in (data.get('tracks') or {}).values():
            sub_url = track.get('url')
            if not sub_url:
                continue
            subtitles.setdefault(track.get('lang') or 'fr', []).append({
                'url': sub_url,
            })

        if not formats:
            fmts, subs = self._get_formats_and_subtitles(url, f'live_{media_id}' if is_live else media_id)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        return {
            'id': media_id,
            'formats': formats,
            'title': title,
            'description': strip_or_none(data.get('description')),
            'thumbnail': data.get('thumbnail'),
            'duration': float_or_none(data.get('realDuration')),
            'timestamp': int_or_none(data.get('liveFrom')),
            'series': data.get('programLabel'),
            'subtitles': subtitles,
            'is_live': is_live,
            '_format_sort_fields': ('res', 'proto'),
        }