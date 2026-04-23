def _real_extract(self, url):
        video_id = self._match_id(url)

        player_config = self._download_json(
            'https://www.smashcast.tv/api/player/config/live/%s' % video_id,
            video_id)

        formats = []
        cdns = player_config.get('cdns')
        servers = []
        for cdn in cdns:
            # Subscribe URLs are not playable
            if cdn.get('rtmpSubscribe') is True:
                continue
            base_url = cdn.get('netConnectionUrl')
            host = re.search(r'.+\.([^\.]+\.[^\./]+)/.+', base_url).group(1)
            if base_url not in servers:
                servers.append(base_url)
                for stream in cdn.get('bitrates'):
                    label = stream.get('label')
                    if label == 'Auto':
                        continue
                    stream_url = stream.get('url')
                    if not stream_url:
                        continue
                    bitrate = int_or_none(stream.get('bitrate'))
                    if stream.get('provider') == 'hls' or determine_ext(stream_url) == 'm3u8':
                        if not stream_url.startswith('http'):
                            continue
                        formats.append({
                            'url': stream_url,
                            'ext': 'mp4',
                            'tbr': bitrate,
                            'format_note': label,
                            'rtmp_live': True,
                        })
                    else:
                        formats.append({
                            'url': '%s/%s' % (base_url, stream_url),
                            'ext': 'mp4',
                            'tbr': bitrate,
                            'rtmp_live': True,
                            'format_note': host,
                            'page_url': url,
                            'player_url': 'http://www.hitbox.tv/static/player/flowplayer/flowplayer.commercial-3.2.16.swf',
                        })
        self._sort_formats(formats)

        metadata = self._extract_metadata(
            'https://www.smashcast.tv/api/media/live', video_id)
        metadata['formats'] = formats
        metadata['is_live'] = True
        metadata['title'] = self._live_title(metadata.get('title'))

        return metadata