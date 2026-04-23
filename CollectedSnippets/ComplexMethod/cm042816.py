def prepare(self, **kwargs):
        assert self.url or self.vid

        if self.url and not self.vid:
            html = get_html(self.url)
            tvid = r1(r'#curid=(.+)_', self.url) or \
                   r1(r'tvid=([^&]+)', self.url) or \
                   r1(r'data-player-tvid="([^"]+)"', html) or r1(r'tv(?:i|I)d=(\w+?)\&', html) or r1(r'param\[\'tvid\'\]\s*=\s*"(.+?)"', html)
            videoid = r1(r'#curid=.+_(.*)$', self.url) or \
                      r1(r'vid=([^&]+)', self.url) or \
                      r1(r'data-player-videoid="([^"]+)"', html) or r1(r'vid=(\w+?)\&', html) or r1(r'param\[\'vid\'\]\s*=\s*"(.+?)"', html)
            self.vid = (tvid, videoid)
            info_u = 'http://pcw-api.iqiyi.com/video/video/playervideoinfo?tvid=' + tvid
            json_res = get_content(info_u)
            self.title = json.loads(json_res)['data']['vn']
        tvid, videoid = self.vid
        info = getVMS(tvid, videoid)
        assert info['code'] == 'A00000', "can't play this video"

        for stream in info['data']['vidl']:
            try:
                stream_id = self.vd_2_id[stream['vd']]
                if stream_id in self.stream_types:
                    continue
                stream_profile = self.id_2_profile[stream_id]
                self.streams[stream_id] = {'video_profile': stream_profile, 'container': 'm3u8', 'src': [stream['m3u']], 'size' : 0, 'm3u8_url': stream['m3u']}
            except Exception as e:
                log.i("vd: {} is not handled".format(stream['vd']))
                log.i("info is {}".format(stream))