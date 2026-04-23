def _real_extract(self, url):
        video_id = self._match_id(url)
        if '-' in video_id:
            return self._extract_yahoo_video(video_id, 'us')

        response = self._download_json(
            'https://feedapi.b2c.on.aol.com/v1.0/app/videos/aolon/%s/details' % video_id,
            video_id)['response']
        if response['statusText'] != 'Ok':
            raise ExtractorError('%s said: %s' % (self.IE_NAME, response['statusText']), expected=True)

        video_data = response['data']
        formats = []
        m3u8_url = url_or_none(video_data.get('videoMasterPlaylist'))
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
        for rendition in video_data.get('renditions', []):
            video_url = url_or_none(rendition.get('url'))
            if not video_url:
                continue
            ext = rendition.get('format')
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
            else:
                f = {
                    'url': video_url,
                    'format_id': rendition.get('quality'),
                }
                mobj = re.search(r'(\d+)x(\d+)', video_url)
                if mobj:
                    f.update({
                        'width': int(mobj.group(1)),
                        'height': int(mobj.group(2)),
                    })
                else:
                    qs = compat_parse_qs(compat_urllib_parse_urlparse(video_url).query)
                    f.update({
                        'width': int_or_none(qs.get('w', [None])[0]),
                        'height': int_or_none(qs.get('h', [None])[0]),
                    })
                formats.append(f)
        self._sort_formats(formats, ('width', 'height', 'tbr', 'format_id'))

        return {
            'id': video_id,
            'title': video_data['title'],
            'duration': int_or_none(video_data.get('duration')),
            'timestamp': int_or_none(video_data.get('publishDate')),
            'view_count': int_or_none(video_data.get('views')),
            'description': video_data.get('description'),
            'uploader': video_data.get('videoOwner'),
            'formats': formats,
        }