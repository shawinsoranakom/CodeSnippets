def prepare(self, **kwargs):
        if self.__class__.coeff is None:
            magic_list = self.__class__.fetch_magic(self.__class__.a_mobile_url)
            self.__class__.coeff = self.__class__.get_coeff(magic_list)

        if 'title' not in kwargs:
            url = 'http://pv.funshion.com/v5/video/profile/?id={}&cl=mweb&uc=111'.format(self.vid)
            meta = json.loads(get_content(url))
            self.title = meta['name']
        else:
            self.title = kwargs['title']

        ep_url = self.__class__.video_ep if 'single_video' in kwargs else self.__class__.media_ep

        url = ep_url.format(self.vid)
        meta = json.loads(get_content(url))
        streams = meta['playlist']
        for stream in streams:
            definition = stream['code']
            for s in stream['playinfo']:
                codec = 'h' + s['codec'][2:]
                # h.264 -> h264
                for st in self.__class__.stream_types:
                    s_id = '{}_{}'.format(definition, codec)
                    if codec == 'h264':
                        s_id = definition
                    if s_id == st['id']:
                        clear_info = self.__class__.dec_playinfo(s, self.__class__.coeff)
                        cdn_list = self.__class__.get_cdninfo(clear_info['hashid'])
                        base_url = cdn_list[0]
                        vf = urllib.parse.quote(s['vf'])
                        video_size = int(s['filesize'])
                        token = urllib.parse.quote(base64.b64encode(clear_info['token'].encode('utf8')))
                        video_url = '{}?token={}&vf={}'.format(base_url, token, vf)
                        self.streams[s_id] = dict(size=video_size, src=[video_url], container='mp4')