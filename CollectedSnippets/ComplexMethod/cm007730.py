def _real_extract(self, url):
        video_id = self._match_id(url)

        params = {
            'initObj': {
                'Locale': {
                    'LocaleLanguage': '',
                    'LocaleCountry': '',
                    'LocaleDevice': '',
                    'LocaleUserState': 0
                },
                'Platform': 0,
                'SiteGuid': 0,
                'DomainID': '0',
                'UDID': '',
                'ApiUser': self._API_USER,
                'ApiPass': self._API_PASS
            },
            'MediaID': video_id,
            'mediaType': 0,
        }

        info = self._download_json(
            'http://tvpapi.as.tvinci.com/v2_9/gateways/jsonpostgw.aspx?m=GetMediaInfo',
            video_id, 'Downloading video info json', data=json.dumps(params).encode('utf-8'))

        title = info['MediaName']

        formats = []
        for video_file in info.get('Files', []):
            video_url, vid_format = video_file.get('URL'), video_file.get('Format')
            if not video_url or video_url == 'NA' or not vid_format:
                continue
            ext = determine_ext(video_url)
            vid_format = vid_format.replace(' ', '')
            # if geo-restricted, m3u8 is inaccessible, but mp4 is okay
            if ext == 'm3u8':
                m3u8_formats = self._extract_m3u8_formats(
                    video_url, video_id, ext='mp4', m3u8_id=vid_format,
                    note='Downloading %s m3u8 information' % vid_format,
                    errnote='Failed to download %s m3u8 information' % vid_format,
                    fatal=False)
                for f in m3u8_formats:
                    # Apple FairPlay Streaming
                    if '/fpshls/' in f['url']:
                        continue
                    formats.append(f)
            elif ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    video_url, video_id, mpd_id=vid_format,
                    note='Downloading %s MPD manifest' % vid_format,
                    errnote='Failed to download %s MPD manifest' % vid_format,
                    fatal=False))
            elif ext == 'ism':
                formats.extend(self._extract_ism_formats(
                    video_url, video_id, ism_id=vid_format,
                    note='Downloading %s ISM manifest' % vid_format,
                    errnote='Failed to download %s ISM manifest' % vid_format,
                    fatal=False))
            elif ext == 'mp4':
                formats.append({
                    'ext': ext,
                    'url': video_url,
                    'format_id': vid_format,
                })
        if not formats:
            for meta in (info.get('Metas') or []):
                if meta.get('Key') == 'Encryption' and meta.get('Value') == '1':
                    raise ExtractorError(
                        'This video is DRM protected.', expected=True)
            # Most likely because geo-blocked
            raise ExtractorError('No downloadable videos found', expected=True)
        self._sort_formats(formats)

        thumbnails = []
        for picture in info.get('Pictures', []):
            if not isinstance(picture, dict):
                continue
            pic_url = picture.get('URL')
            if not pic_url:
                continue
            thumbnail = {
                'url': pic_url,
            }
            pic_size = picture.get('PicSize', '')
            m = re.search(r'(?P<width>\d+)[xX](?P<height>\d+)', pic_size)
            if m:
                thumbnail.update({
                    'width': int(m.group('width')),
                    'height': int(m.group('height')),
                })
            thumbnails.append(thumbnail)

        def counter(prefix):
            return int_or_none(
                info.get(prefix + 'Counter') or info.get(prefix.lower() + '_counter'))

        return {
            'id': video_id,
            'title': title,
            'description': strip_or_none(info.get('Description')),
            'duration': int_or_none(info.get('Duration')),
            'timestamp': parse_iso8601(info.get('CreationDate') or None),
            'average_rating': float_or_none(info.get('Rating')),
            'view_count': counter('View'),
            'like_count': counter('Like'),
            'thumbnails': thumbnails,
            'formats': formats,
        }