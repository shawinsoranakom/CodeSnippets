def _real_extract(self, url):
        channel_id = self._match_id(url)

        data = self._download_json(
            'https://ptvintern.picarto.tv/ptvapi', channel_id, query={
                'query': '''{
  channel(name: "%s") {
    adult
    id
    online
    stream_name
    title
  }
  getLoadBalancerUrl(channel_name: "%s") {
    url
  }
}''' % (channel_id, channel_id),
            })['data']
        metadata = data['channel']

        if metadata.get('online') == 0:
            raise ExtractorError('Stream is offline', expected=True)
        title = metadata['title']

        cdn_data = self._download_json(
            data['getLoadBalancerUrl']['url'] + '/stream/json_' + metadata['stream_name'] + '.js',
            channel_id, 'Downloading load balancing info')

        formats = []
        for source in (cdn_data.get('source') or []):
            source_url = source.get('url')
            if not source_url:
                continue
            source_type = source.get('type')
            if source_type == 'html5/application/vnd.apple.mpegurl':
                formats.extend(self._extract_m3u8_formats(
                    source_url, channel_id, 'mp4', m3u8_id='hls', fatal=False))
            elif source_type == 'html5/video/mp4':
                formats.append({
                    'url': source_url,
                })
        self._sort_formats(formats)

        mature = metadata.get('adult')
        if mature is None:
            age_limit = None
        else:
            age_limit = 18 if mature is True else 0

        return {
            'id': channel_id,
            'title': self._live_title(title.strip()),
            'is_live': True,
            'channel': channel_id,
            'channel_id': metadata.get('id'),
            'channel_url': 'https://picarto.tv/%s' % channel_id,
            'age_limit': age_limit,
            'formats': formats,
        }