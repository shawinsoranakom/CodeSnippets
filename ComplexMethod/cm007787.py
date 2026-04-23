def _real_extract(self, url):
        channel_id = self._match_id(url)

        try:
            channel_data = self._download_json(
                'http://www.filmon.com/api-v2/channel/' + channel_id, channel_id)['data']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError):
                errmsg = self._parse_json(e.cause.read().decode(), channel_id)['message']
                raise ExtractorError('%s said: %s' % (self.IE_NAME, errmsg), expected=True)
            raise

        channel_id = compat_str(channel_data['id'])
        is_live = not channel_data.get('is_vod') and not channel_data.get('is_vox')
        title = channel_data['title']

        QUALITY = qualities(('low', 'high'))
        formats = []
        for stream in channel_data.get('streams', []):
            stream_url = stream.get('url')
            if not stream_url:
                continue
            if not is_live:
                formats.extend(self._extract_wowza_formats(
                    stream_url, channel_id, skip_protocols=['dash', 'rtmp', 'rtsp']))
                continue
            quality = stream.get('quality')
            formats.append({
                'format_id': quality,
                # this is an m3u8 stream, but we are deliberately not using _extract_m3u8_formats
                # because it doesn't have bitrate variants anyway
                'url': stream_url,
                'ext': 'mp4',
                'quality': QUALITY(quality),
            })
        self._sort_formats(formats)

        thumbnails = []
        for name, width, height in self._THUMBNAIL_RES:
            thumbnails.append({
                'id': name,
                'url': 'http://static.filmon.com/assets/channels/%s/%s.png' % (channel_id, name),
                'width': width,
                'height': height,
            })

        return {
            'id': channel_id,
            'display_id': channel_data.get('alias'),
            'title': self._live_title(title) if is_live else title,
            'description': channel_data.get('description'),
            'thumbnails': thumbnails,
            'formats': formats,
            'is_live': is_live,
        }