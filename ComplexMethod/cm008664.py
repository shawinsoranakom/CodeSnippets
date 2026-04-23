def _real_extract(self, url):

        def _fetch_data(vid_id, mytv=False):
            if mytv:
                base_data_url = 'http://my.tv.sohu.com/play/videonew.do?vid='
            else:
                base_data_url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid='

            return self._download_json(
                base_data_url + vid_id, video_id,
                f'Downloading JSON data for {vid_id}',
                headers=self.geo_verification_headers())

        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')
        mytv = mobj.group('mytv') is not None

        webpage = self._download_webpage(url, video_id)

        title = re.sub(r'( - 高清正版在线观看)? - 搜狐视频$', '', self._og_search_title(webpage))

        vid = self._html_search_regex(
            r'var vid ?= ?["\'](\d+)["\']',
            webpage, 'video path')
        vid_data = _fetch_data(vid, mytv)
        if vid_data['play'] != 1:
            if vid_data.get('status') == 12:
                raise ExtractorError(
                    f'{self.IE_NAME} said: There\'s something wrong in the video.',
                    expected=True)
            else:
                self.raise_geo_restricted(
                    f'{self.IE_NAME} said: The video is only licensed to users in Mainland China.')

        formats_json = {}
        for format_id in ('nor', 'high', 'super', 'ori', 'h2644k', 'h2654k'):
            vid_id = vid_data['data'].get(f'{format_id}Vid')
            if not vid_id:
                continue
            vid_id = str(vid_id)
            formats_json[format_id] = vid_data if vid == vid_id else _fetch_data(vid_id, mytv)

        part_count = vid_data['data']['totalBlocks']

        playlist = []
        for i in range(part_count):
            formats = []
            for format_id, format_data in formats_json.items():
                allot = format_data['allot']

                data = format_data['data']
                clip_url = traverse_obj(data, (('clipsURL', 'mp4PlayUrl'), i, {url_or_none}), get_all=False)
                if not clip_url:
                    raise ExtractorError(f'Unable to extract url for clip {i}')
                su = data['su']

                video_url = 'newflv.sohu.ccgslb.net'
                cdn_id = None
                retries = 0

                while 'newflv.sohu.ccgslb.net' in video_url:
                    params = {
                        'prot': 9,
                        'file': clip_url,
                        'new': su[i],
                        'prod': 'h5n',
                        'rb': 1,
                    }

                    if cdn_id is not None:
                        params['idc'] = cdn_id

                    download_note = f'Downloading {format_id} video URL part {i + 1} of {part_count}'

                    if retries > 0:
                        download_note += f' (retry #{retries})'
                    part_info = self._parse_json(self._download_webpage(
                        f'http://{allot}/?{urllib.parse.urlencode(params)}',
                        video_id, download_note), video_id)

                    video_url = part_info['url']
                    cdn_id = part_info.get('nid')

                    retries += 1
                    if retries > 5:
                        raise ExtractorError('Failed to get video URL')

                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'filesize': int_or_none(
                        try_get(data, lambda x: x['clipsBytes'][i])),
                    'width': int_or_none(data.get('width')),
                    'height': int_or_none(data.get('height')),
                    'fps': int_or_none(data.get('fps')),
                })

            playlist.append({
                'id': f'{video_id}_part{i + 1}',
                'title': title,
                'duration': vid_data['data']['clipsDuration'][i],
                'formats': formats,
            })

        if len(playlist) == 1:
            info = playlist[0]
            info['id'] = video_id
        else:
            info = {
                '_type': 'multi_video',
                'entries': playlist,
                'id': video_id,
                'title': title,
                'duration': traverse_obj(vid_data, ('data', 'totalDuration', {float_or_none})),
            }

        if mytv:
            publish_time = unified_timestamp(self._search_regex(
                r'publishTime:\s*["\'](\d+-\d+-\d+ \d+:\d+)["\']', webpage, 'publish time', fatal=False))
        else:
            publish_time = traverse_obj(vid_data, ('tv_application_time', {unified_timestamp}))

        return {
            'timestamp': publish_time - 8 * 3600 if publish_time else None,
            **traverse_obj(vid_data, {
                'alt_title': ('data', 'subName', {str}),
                'uploader': ('wm_data', 'wm_username', {str}),
                'thumbnail': ('data', 'coverImg', {url_or_none}),
                'tags': ('data', 'tag', {str.split}),
            }),
            **info,
        }