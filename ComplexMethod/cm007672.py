def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')

        if mobj.group('prefix') == 'm':
            mobile_webpage = self._download_webpage(url, video_id, 'Downloading mobile webpage')
            webpage_url = self._search_regex(r'<link rel="canonical" href="([^"]+)" />', mobile_webpage, 'webpage_url')
        else:
            webpage_url = 'http://www.' + mobj.group('url')

        webpage = self._download_webpage(
            self._add_skip_wall(webpage_url), video_id,
            headers=self.geo_verification_headers())
        note_m = self._html_search_regex(
            r'<div class="showmedia-trailer-notice">(.+?)</div>',
            webpage, 'trailer-notice', default='')
        if note_m:
            raise ExtractorError(note_m)

        mobj = re.search(r'Page\.messaging_box_controller\.addItems\(\[(?P<msg>{.+?})\]\)', webpage)
        if mobj:
            msg = json.loads(mobj.group('msg'))
            if msg.get('type') == 'error':
                raise ExtractorError('crunchyroll returned error: %s' % msg['message_body'], expected=True)

        if 'To view this, please log in to verify you are 18 or older.' in webpage:
            self.raise_login_required()

        media = self._parse_json(self._search_regex(
            r'vilos\.config\.media\s*=\s*({.+?});',
            webpage, 'vilos media', default='{}'), video_id)
        media_metadata = media.get('metadata') or {}

        language = self._search_regex(
            r'(?:vilos\.config\.player\.language|LOCALE)\s*=\s*(["\'])(?P<lang>(?:(?!\1).)+)\1',
            webpage, 'language', default=None, group='lang')

        video_title = self._html_search_regex(
            (r'(?s)<h1[^>]*>((?:(?!<h1).)*?<(?:span[^>]+itemprop=["\']title["\']|meta[^>]+itemprop=["\']position["\'])[^>]*>(?:(?!<h1).)+?)</h1>',
             r'<title>(.+?),\s+-\s+.+? Crunchyroll'),
            webpage, 'video_title', default=None)
        if not video_title:
            video_title = re.sub(r'^Watch\s+', '', self._og_search_description(webpage))
        video_title = re.sub(r' {2,}', ' ', video_title)
        video_description = (self._parse_json(self._html_search_regex(
            r'<script[^>]*>\s*.+?\[media_id=%s\].+?({.+?"description"\s*:.+?})\);' % video_id,
            webpage, 'description', default='{}'), video_id) or media_metadata).get('description')
        if video_description:
            video_description = lowercase_escape(video_description.replace(r'\r\n', '\n'))
        video_uploader = self._html_search_regex(
            # try looking for both an uploader that's a link and one that's not
            [r'<a[^>]+href="/publisher/[^"]+"[^>]*>([^<]+)</a>', r'<div>\s*Publisher:\s*<span>\s*(.+?)\s*</span>\s*</div>'],
            webpage, 'video_uploader', default=False)

        formats = []
        for stream in media.get('streams', []):
            audio_lang = stream.get('audio_lang')
            hardsub_lang = stream.get('hardsub_lang')
            vrv_formats = self._extract_vrv_formats(
                stream.get('url'), video_id, stream.get('format'),
                audio_lang, hardsub_lang)
            for f in vrv_formats:
                if not hardsub_lang:
                    f['preference'] = 1
                language_preference = 0
                if audio_lang == language:
                    language_preference += 1
                if hardsub_lang == language:
                    language_preference += 1
                if language_preference:
                    f['language_preference'] = language_preference
            formats.extend(vrv_formats)
        if not formats:
            available_fmts = []
            for a, fmt in re.findall(r'(<a[^>]+token=["\']showmedia\.([0-9]{3,4})p["\'][^>]+>)', webpage):
                attrs = extract_attributes(a)
                href = attrs.get('href')
                if href and '/freetrial' in href:
                    continue
                available_fmts.append(fmt)
            if not available_fmts:
                for p in (r'token=["\']showmedia\.([0-9]{3,4})p"', r'showmedia\.([0-9]{3,4})p'):
                    available_fmts = re.findall(p, webpage)
                    if available_fmts:
                        break
            if not available_fmts:
                available_fmts = self._FORMAT_IDS.keys()
            video_encode_ids = []

            for fmt in available_fmts:
                stream_quality, stream_format = self._FORMAT_IDS[fmt]
                video_format = fmt + 'p'
                stream_infos = []
                streamdata = self._call_rpc_api(
                    'VideoPlayer_GetStandardConfig', video_id,
                    'Downloading media info for %s' % video_format, data={
                        'media_id': video_id,
                        'video_format': stream_format,
                        'video_quality': stream_quality,
                        'current_page': url,
                    })
                if isinstance(streamdata, compat_etree_Element):
                    stream_info = streamdata.find('./{default}preload/stream_info')
                    if stream_info is not None:
                        stream_infos.append(stream_info)
                stream_info = self._call_rpc_api(
                    'VideoEncode_GetStreamInfo', video_id,
                    'Downloading stream info for %s' % video_format, data={
                        'media_id': video_id,
                        'video_format': stream_format,
                        'video_encode_quality': stream_quality,
                    })
                if isinstance(stream_info, compat_etree_Element):
                    stream_infos.append(stream_info)
                for stream_info in stream_infos:
                    video_encode_id = xpath_text(stream_info, './video_encode_id')
                    if video_encode_id in video_encode_ids:
                        continue
                    video_encode_ids.append(video_encode_id)

                    video_file = xpath_text(stream_info, './file')
                    if not video_file:
                        continue
                    if video_file.startswith('http'):
                        formats.extend(self._extract_m3u8_formats(
                            video_file, video_id, 'mp4', entry_protocol='m3u8_native',
                            m3u8_id='hls', fatal=False))
                        continue

                    video_url = xpath_text(stream_info, './host')
                    if not video_url:
                        continue
                    metadata = stream_info.find('./metadata')
                    format_info = {
                        'format': video_format,
                        'height': int_or_none(xpath_text(metadata, './height')),
                        'width': int_or_none(xpath_text(metadata, './width')),
                    }

                    if '.fplive.net/' in video_url:
                        video_url = re.sub(r'^rtmpe?://', 'http://', video_url.strip())
                        parsed_video_url = compat_urlparse.urlparse(video_url)
                        direct_video_url = compat_urlparse.urlunparse(parsed_video_url._replace(
                            netloc='v.lvlt.crcdn.net',
                            path='%s/%s' % (remove_end(parsed_video_url.path, '/'), video_file.split(':')[-1])))
                        if self._is_valid_url(direct_video_url, video_id, video_format):
                            format_info.update({
                                'format_id': 'http-' + video_format,
                                'url': direct_video_url,
                            })
                            formats.append(format_info)
                            continue

                    format_info.update({
                        'format_id': 'rtmp-' + video_format,
                        'url': video_url,
                        'play_path': video_file,
                        'ext': 'flv',
                    })
                    formats.append(format_info)
        self._sort_formats(formats, ('preference', 'language_preference', 'height', 'width', 'tbr', 'fps'))

        metadata = self._call_rpc_api(
            'VideoPlayer_GetMediaMetadata', video_id,
            note='Downloading media info', data={
                'media_id': video_id,
            })

        subtitles = {}
        for subtitle in media.get('subtitles', []):
            subtitle_url = subtitle.get('url')
            if not subtitle_url:
                continue
            subtitles.setdefault(subtitle.get('language', 'enUS'), []).append({
                'url': subtitle_url,
                'ext': subtitle.get('format', 'ass'),
            })
        if not subtitles:
            subtitles = self.extract_subtitles(video_id, webpage)

        # webpage provide more accurate data than series_title from XML
        series = self._html_search_regex(
            r'(?s)<h\d[^>]+\bid=["\']showmedia_about_episode_num[^>]+>(.+?)</h\d',
            webpage, 'series', fatal=False)

        season = episode = episode_number = duration = thumbnail = None

        if isinstance(metadata, compat_etree_Element):
            season = xpath_text(metadata, 'series_title')
            episode = xpath_text(metadata, 'episode_title')
            episode_number = int_or_none(xpath_text(metadata, 'episode_number'))
            duration = float_or_none(media_metadata.get('duration'), 1000)
            thumbnail = xpath_text(metadata, 'episode_image_url')

        if not episode:
            episode = media_metadata.get('title')
        if not episode_number:
            episode_number = int_or_none(media_metadata.get('episode_number'))
        if not thumbnail:
            thumbnail = media_metadata.get('thumbnail', {}).get('url')

        season_number = int_or_none(self._search_regex(
            r'(?s)<h\d[^>]+id=["\']showmedia_about_episode_num[^>]+>.+?</h\d>\s*<h4>\s*Season (\d+)',
            webpage, 'season number', default=None))

        info = self._search_json_ld(webpage, video_id, default={})

        return merge_dicts({
            'id': video_id,
            'title': video_title,
            'description': video_description,
            'duration': duration,
            'thumbnail': thumbnail,
            'uploader': video_uploader,
            'series': series,
            'season': season,
            'season_number': season_number,
            'episode': episode,
            'episode_number': episode_number,
            'subtitles': subtitles,
            'formats': formats,
        }, info)