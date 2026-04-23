def _real_extract(self, url):
        channel_id, broadcast_id = re.match(self._VALID_URL, url).groups()
        broadcast = self._download_json(
            self._API_BASE_URL + '%s/broadcast/%s' % (channel_id, broadcast_id),
            broadcast_id)
        item = broadcast['item']
        info = self._parse_broadcast_item(item)
        protocol = 'm3u8' if info['is_live'] else 'm3u8_native'
        formats = []
        for k, v in (broadcast.get(('live' if info['is_live'] else 'archived') + 'HLSURLs') or {}).items():
            if not v:
                continue
            if k == 'abr':
                formats.extend(self._extract_m3u8_formats(
                    v, broadcast_id, 'mp4', protocol,
                    m3u8_id='hls', fatal=False))
                continue
            f = {
                'ext': 'mp4',
                'format_id': 'hls-' + k,
                'protocol': protocol,
                'url': v,
            }
            if not k.isdigit():
                f['vcodec'] = 'none'
            formats.append(f)
        if not formats:
            archive_status = item.get('archiveStatus')
            if archive_status != 'ARCHIVED':
                raise ExtractorError('this video has been ' + archive_status.lower(), expected=True)
        self._sort_formats(formats)
        info['formats'] = formats
        return info