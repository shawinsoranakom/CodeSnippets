def prepare(self, **kwargs):
        assert self.url or self.vid

        if self.url and not self.vid:
            self.get_vid_from_url()

            if self.vid is None:
                self.get_vid_from_page()

                if self.vid is None:
                    log.wtf('Cannot fetch vid')

        if kwargs.get('src') and kwargs['src'] == 'tudou':
            self.ccode = '0512'

        if kwargs.get('password') and kwargs['password']:
            self.password_protected = True
            self.password = kwargs['password']

        self.utid = fetch_cna()
        time.sleep(3)
        self.youku_ups()

        if self.api_data.get('stream') is None:
            if self.api_error_code == -6001:  # wrong vid parsed from the page
                vid_from_url = self.vid
                self.get_vid_from_page()
                if vid_from_url == self.vid:
                    log.wtf(self.api_error_msg)
                self.youku_ups()

        if self.api_data.get('stream') is None:
            if self.api_error_code == -2002:  # wrong password
                self.password_protected = True
                # it can be True already(from cli). offer another chance to retry
                self.password = input(log.sprint('Password: ', log.YELLOW))
                self.youku_ups()

        if self.api_data.get('stream') is None:
            if self.api_error_msg:
                log.wtf(self.api_error_msg)
            else:
                log.wtf('Unknown error')

        self.title = self.api_data['video']['title']
        stream_types = dict([(i['id'], i) for i in self.stream_types])
        audio_lang = self.api_data['stream'][0]['audio_lang']

        for stream in self.api_data['stream']:
            stream_id = stream['stream_type']
            is_preview = False
            if stream_id in stream_types and stream['audio_lang'] == audio_lang:
                if 'alias-of' in stream_types[stream_id]:
                    stream_id = stream_types[stream_id]['alias-of']

                if stream_id not in self.streams:
                    self.streams[stream_id] = {
                        'container': stream_types[stream_id]['container'],
                        'video_profile': stream_types[stream_id]['video_profile'],
                        'size': stream['size'],
                        'pieces': [{
                            'segs': stream['segs']
                        }],
                        'm3u8_url': stream['m3u8_url']
                    }
                    src = []
                    for seg in stream['segs']:
                        if seg.get('cdn_url'):
                            src.append(self.__class__.change_cdn(seg['cdn_url']))
                        else:
                            is_preview = True
                    self.streams[stream_id]['src'] = src
                else:
                    self.streams[stream_id]['size'] += stream['size']
                    self.streams[stream_id]['pieces'].append({
                        'segs': stream['segs']
                    })
                    src = []
                    for seg in stream['segs']:
                        if seg.get('cdn_url'):
                            src.append(self.__class__.change_cdn(seg['cdn_url']))
                        else:
                            is_preview = True
                    self.streams[stream_id]['src'].extend(src)
            if is_preview:
                log.w('{} is a preview'.format(stream_id))

        # Audio languages
        if 'dvd' in self.api_data:
            al = self.api_data['dvd'].get('audiolang')
            if al:
                self.audiolang = al
                for i in self.audiolang:
                    i['url'] = 'http://v.youku.com/v_show/id_{}'.format(i['vid'])