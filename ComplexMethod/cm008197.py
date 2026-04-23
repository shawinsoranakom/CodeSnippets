def _real_extract(self, url):
        video_id = self._match_id(url)

        self._set_cookie('youku.com', '__ysuid', self.get_ysuid())
        self._set_cookie('youku.com', 'xreferrer', 'http://www.youku.com')

        _, urlh = self._download_webpage_handle(
            'https://log.mmstat.com/eg.js', video_id, 'Retrieving cna info')
        # The etag header is '"foobar"'; let's remove the double quotes
        cna = urlh.headers['etag'][1:-1]

        # request basic data
        basic_data_params = {
            'vid': video_id,
            'ccode': '0564',
            'client_ip': '192.168.1.1',
            'utid': cna,
            'client_ts': time.time() / 1000,
        }

        video_password = self.get_param('videopassword')
        if video_password:
            basic_data_params['password'] = video_password

        headers = {
            'Referer': url,
        }
        headers.update(self.geo_verification_headers())
        data = self._download_json(
            'https://ups.youku.com/ups/get.json', video_id,
            'Downloading JSON metadata',
            query=basic_data_params, headers=headers)['data']

        error = data.get('error')
        if error:
            error_note = error.get('note')
            if error_note is not None and '因版权原因无法观看此视频' in error_note:
                raise ExtractorError(
                    'Youku said: Sorry, this video is available in China only', expected=True)
            elif error_note and '该视频被设为私密' in error_note:
                raise ExtractorError(
                    'Youku said: Sorry, this video is private', expected=True)
            else:
                msg = 'Youku server reported error %i' % error.get('code')
                if error_note is not None:
                    msg += ': ' + clean_html(error_note)
                raise ExtractorError(msg)

        # get video title
        video_data = data['video']
        title = video_data['title']

        formats = [{
            'url': stream['m3u8_url'],
            'format_id': self.get_format_name(stream.get('stream_type')),
            'ext': 'mp4',
            'protocol': 'm3u8_native',
            'filesize': int(stream.get('size')),
            'width': stream.get('width'),
            'height': stream.get('height'),
        } for stream in data['stream'] if stream.get('channel_type') != 'tail']

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'duration': video_data.get('seconds'),
            'thumbnail': video_data.get('logo'),
            'uploader': video_data.get('username'),
            'uploader_id': str_or_none(video_data.get('userid')),
            'uploader_url': data.get('uploader', {}).get('homepage'),
            'tags': video_data.get('tags'),
        }