def _real_extract(self, url):
        mid = self._match_id(url)

        init_data = self._download_init_data(url, mid, fatal=False)
        info_data = self._make_fcu_req({'info': {
            'module': 'music.pf_song_detail_svr',
            'method': 'get_song_detail_yqq',
            'param': {
                'song_mid': mid,
                'song_type': 0,
            },
        }}, mid, note='Downloading song info')['info']['data']['track_info']

        media_mid = info_data['file']['media_mid']

        data = self._make_fcu_req({
            'req_1': {
                'module': 'vkey.GetVkeyServer',
                'method': 'CgiGetVkey',
                'param': {
                    'guid': str(self._m_r_get_ruin()),
                    'songmid': [mid] * len(self._FORMATS),
                    'songtype': [0] * len(self._FORMATS),
                    'uin': str(self._get_uin()),
                    'loginflag': 1,
                    'platform': '20',
                    'filename': [f'{f["prefix"]}{media_mid}.{f["ext"]}' for f in self._FORMATS.values()],
                },
            },
            'req_2': {
                'module': 'music.musichallSong.PlayLyricInfo',
                'method': 'GetPlayLyricInfo',
                'param': {'songMID': mid},
            },
        }, mid, note='Downloading formats and lyric', headers=self.geo_verification_headers())

        code = traverse_obj(data, ('req_1', 'code', {int}))
        if code != 0:
            raise ExtractorError(f'Failed to download format info, error code {code or "unknown"}')
        formats = []
        for media_info in traverse_obj(data, (
            'req_1', 'data', 'midurlinfo', lambda _, v: v['songmid'] == mid and v['purl']),
        ):
            format_key = traverse_obj(media_info, ('filename', {str}, {lambda x: x[:4]}))
            format_info = self._FORMATS.get(format_key) or {}
            format_id = format_info.get('name')
            formats.append({
                'url': urljoin('https://dl.stream.qqmusic.qq.com', media_info['purl']),
                'format': format_id,
                'format_id': format_id,
                'size': traverse_obj(info_data, ('file', f'size_{format_id}', {int_or_none})),
                'quality': format_info.get('preference'),
                'abr': format_info.get('abr'),
                'ext': format_info.get('ext'),
                'vcodec': 'none',
            })

        if not formats and not self.is_logged_in:
            self.raise_login_required()

        if traverse_obj(data, ('req_2', 'code')):
            self.report_warning(f'Failed to download lyric, error {data["req_2"]["code"]!r}')
        lrc_content = traverse_obj(data, ('req_2', 'data', 'lyric', {lambda x: base64.b64decode(x).decode('utf-8')}))

        info_dict = {
            'id': mid,
            'formats': formats,
            **traverse_obj(info_data, {
                'title': ('title', {str}),
                'album': ('album', 'title', {str}, filter),
                'release_date': ('time_public', {lambda x: x.replace('-', '') or None}),
                'creators': ('singer', ..., 'name', {str}),
                'alt_title': ('subtitle', {str}, filter),
                'duration': ('interval', {int_or_none}),
            }),
            **traverse_obj(init_data, ('detail', {
                'thumbnail': ('picurl', {url_or_none}),
                'description': ('info', 'intro', 'content', ..., 'value', {str}),
                'genres': ('info', 'genre', 'content', ..., 'value', {str}, all),
            }), get_all=False),
        }
        if lrc_content:
            info_dict['subtitles'] = {'origin': [{'ext': 'lrc', 'data': lrc_content}]}
            info_dict['description'] = join_nonempty(info_dict.get('description'), lrc_content, delim='\n')
        return info_dict