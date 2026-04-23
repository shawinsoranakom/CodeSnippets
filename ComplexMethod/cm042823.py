def prepare_by_cid(self,avid,cid,title,html_content,playinfo,playinfo_,url):
        #response for interaction video
        #主要针对互动视频，使用cid而不是url来相互区分

        self.stream_qualities = {s['quality']: s for s in self.stream_types}
        self.title = title
        self.url = url

        current_quality, best_quality = None, None
        if playinfo is not None:
            current_quality = playinfo['data']['quality'] or None  # 0 indicates an error, fallback to None
            if 'accept_quality' in playinfo['data'] and playinfo['data']['accept_quality'] != []:
                best_quality = playinfo['data']['accept_quality'][0]
        playinfos = []
        if playinfo is not None:
            playinfos.append(playinfo)
        if playinfo_ is not None:
            playinfos.append(playinfo_)
        # get alternative formats from API
        for qn in [80, 64, 32, 16]:
            # automatic format for durl: qn=0
            # for dash, qn does not matter
            if current_quality is None or qn < current_quality:
                api_url = self.bilibili_api(avid, cid, qn=qn)
                api_content = get_content(api_url, headers=self.bilibili_headers())
                api_playinfo = json.loads(api_content)
                if api_playinfo['code'] == 0:  # success
                    playinfos.append(api_playinfo)
                else:
                    message = api_playinfo['data']['message']
            if best_quality is None or qn <= best_quality:
                api_url = self.bilibili_interface_api(cid, qn=qn)
                api_content = get_content(api_url, headers=self.bilibili_headers())
                api_playinfo_data = json.loads(api_content)
                if api_playinfo_data.get('quality'):
                    playinfos.append({'code': 0, 'message': '0', 'ttl': 1, 'data': api_playinfo_data})
        if not playinfos:
            log.w(message)
            # use bilibili error video instead
            url = 'https://static.hdslb.com/error.mp4'
            _, container, size = url_info(url)
            self.streams['flv480'] = {'container': container, 'size': size, 'src': [url]}
            return

        for playinfo in playinfos:
            quality = playinfo['data']['quality']
            format_id = self.stream_qualities[quality]['id']
            container = self.stream_qualities[quality]['container'].lower()
            desc = self.stream_qualities[quality]['desc']

            if 'durl' in playinfo['data']:
                src, size = [], 0
                for durl in playinfo['data']['durl']:
                    src.append(durl['url'])
                    size += durl['size']
                self.streams[format_id] = {'container': container, 'quality': desc, 'size': size, 'src': src}

            # DASH formats
            if 'dash' in playinfo['data']:
                audio_size_cache = {}
                for video in playinfo['data']['dash']['video']:
                    # prefer the latter codecs!
                    s = self.stream_qualities[video['id']]
                    format_id = 'dash-' + s['id']  # prefix
                    container = 'mp4'  # enforce MP4 container
                    desc = s['desc']
                    audio_quality = s['audio_quality']
                    baseurl = video['baseUrl']
                    size = self.url_size(baseurl, headers=self.bilibili_headers(referer=self.url))

                    # find matching audio track
                    if playinfo['data']['dash']['audio']:
                        audio_baseurl = playinfo['data']['dash']['audio'][0]['baseUrl']
                        for audio in playinfo['data']['dash']['audio']:
                            if int(audio['id']) == audio_quality:
                                audio_baseurl = audio['baseUrl']
                                break
                        if not audio_size_cache.get(audio_quality, False):
                            audio_size_cache[audio_quality] = self.url_size(audio_baseurl,
                                                                            headers=self.bilibili_headers(referer=self.url))
                        size += audio_size_cache[audio_quality]

                        self.dash_streams[format_id] = {'container': container, 'quality': desc,
                                                        'src': [[baseurl], [audio_baseurl]], 'size': size}
                    else:
                        self.dash_streams[format_id] = {'container': container, 'quality': desc,
                                                        'src': [[baseurl]], 'size': size}

        # get danmaku
        self.danmaku = get_content('https://comment.bilibili.com/%s.xml' % cid, headers=self.bilibili_headers(referer=self.url))