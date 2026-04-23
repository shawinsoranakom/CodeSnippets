def extract_info(self, video_id):
        session = self._download_json(
            'https://api.redbull.tv/v3/session', video_id,
            note='Downloading access token', query={
                'category': 'personal_computer',
                'os_family': 'http',
            })
        if session.get('code') == 'error':
            raise ExtractorError('%s said: %s' % (
                self.IE_NAME, session['message']))
        token = session['token']

        try:
            video = self._download_json(
                'https://api.redbull.tv/v3/products/' + video_id,
                video_id, note='Downloading video information',
                headers={'Authorization': token}
            )
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 404:
                error_message = self._parse_json(
                    e.cause.read().decode(), video_id)['error']
                raise ExtractorError('%s said: %s' % (
                    self.IE_NAME, error_message), expected=True)
            raise

        title = video['title'].strip()

        formats = self._extract_m3u8_formats(
            'https://dms.redbull.tv/v3/%s/%s/playlist.m3u8' % (video_id, token),
            video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        subtitles = {}
        for resource in video.get('resources', []):
            if resource.startswith('closed_caption_'):
                splitted_resource = resource.split('_')
                if splitted_resource[2]:
                    subtitles.setdefault('en', []).append({
                        'url': 'https://resources.redbull.tv/%s/%s' % (video_id, resource),
                        'ext': splitted_resource[2],
                    })

        subheading = video.get('subheading')
        if subheading:
            title += ' - %s' % subheading

        return {
            'id': video_id,
            'title': title,
            'description': video.get('long_description') or video.get(
                'short_description'),
            'duration': float_or_none(video.get('duration'), scale=1000),
            'formats': formats,
            'subtitles': subtitles,
        }