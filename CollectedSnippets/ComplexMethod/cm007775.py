def _real_extract(self, url):
        domain, video_id, display_id = re.match(self._VALID_URL, url).groups()
        if not video_id:
            webpage = self._download_webpage(url, display_id)
            grill = re.sub(r'"\s*\+\s*"', '', self._search_regex(
                r'Grill\.burger\s*=\s*({.+})\s*:',
                webpage, 'grill data'))
            page_data = next(s for s in self._parse_json(grill, display_id)['stack'] if s.get('type') == 'video')
            video_data = page_data['data'][0]
        else:
            webpage = self._download_webpage(
                'http://%s/embed/%s' % (domain, video_id), video_id)
            page_data = self._parse_json(self._search_regex(
                r'Disney\.EmbedVideo\s*=\s*({.+});',
                webpage, 'embed data'), video_id)
            video_data = page_data['video']

        for external in video_data.get('externals', []):
            if external.get('source') == 'vevo':
                return self.url_result('vevo:' + external['data_id'], 'Vevo')

        video_id = video_data['id']
        title = video_data['title']

        formats = []
        for flavor in video_data.get('flavors', []):
            flavor_format = flavor.get('format')
            flavor_url = flavor.get('url')
            if not flavor_url or not re.match(r'https?://', flavor_url) or flavor_format == 'mp4_access':
                continue
            tbr = int_or_none(flavor.get('bitrate'))
            if tbr == 99999:
                # wrong ks(Kaltura Signature) causes 404 Error
                flavor_url = update_url_query(flavor_url, {'ks': ''})
                m3u8_formats = self._extract_m3u8_formats(
                    flavor_url, video_id, 'mp4',
                    m3u8_id=flavor_format, fatal=False)
                for f in m3u8_formats:
                    # Apple FairPlay
                    if '/fpshls/' in f['url']:
                        continue
                    formats.append(f)
                continue
            format_id = []
            if flavor_format:
                format_id.append(flavor_format)
            if tbr:
                format_id.append(compat_str(tbr))
            ext = determine_ext(flavor_url)
            if flavor_format == 'applehttp' or ext == 'm3u8':
                ext = 'mp4'
            width = int_or_none(flavor.get('width'))
            height = int_or_none(flavor.get('height'))
            formats.append({
                'format_id': '-'.join(format_id),
                'url': flavor_url,
                'width': width,
                'height': height,
                'tbr': tbr,
                'ext': ext,
                'vcodec': 'none' if (width == 0 and height == 0) else None,
            })
        if not formats and video_data.get('expired'):
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, page_data['translations']['video_expired']),
                expected=True)
        self._sort_formats(formats)

        subtitles = {}
        for caption in video_data.get('captions', []):
            caption_url = caption.get('url')
            caption_format = caption.get('format')
            if not caption_url or caption_format.startswith('unknown'):
                continue
            subtitles.setdefault(caption.get('language', 'en'), []).append({
                'url': caption_url,
                'ext': {
                    'webvtt': 'vtt',
                }.get(caption_format, caption_format),
            })

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description') or video_data.get('short_desc'),
            'thumbnail': video_data.get('thumb') or video_data.get('thumb_secure'),
            'duration': int_or_none(video_data.get('duration_sec')),
            'upload_date': unified_strdate(video_data.get('publish_date')),
            'formats': formats,
            'subtitles': subtitles,
        }