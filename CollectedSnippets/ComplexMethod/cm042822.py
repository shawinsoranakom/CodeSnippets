def prepare(self, **kwargs):
        self.stream_qualities = {s['quality']: s for s in self.stream_types}
        self.streams.clear()
        self.dash_streams.clear()

        try:
            html_content = get_content(self.url, headers=self.bilibili_headers(referer=self.url))
        except:
            html_content = ''  # live always returns 400 (why?)
        #self.title = match1(html_content,
        #                    r'<h1 title="([^"]+)"')

        # redirect: watchlater
        if re.match(r'https?://(www\.)?bilibili\.com/watchlater/#/(av(\d+)|BV(\S+)/?)', self.url):
            avid = match1(self.url, r'/(av\d+)') or match1(self.url, r'/(BV\w+)')
            p = int(match1(self.url, r'/p(\d+)') or '1')
            self.url = 'https://www.bilibili.com/video/%s?p=%s' % (avid, p)
            html_content = get_content(self.url, headers=self.bilibili_headers())

        # redirect: bangumi/play/ss -> bangumi/play/ep
        # redirect: bangumi.bilibili.com/anime -> bangumi/play/ep
        elif re.match(r'https?://(www\.)?bilibili\.com/bangumi/play/ss(\d+)', self.url) or \
             re.match(r'https?://bangumi\.bilibili\.com/anime/(\d+)/play', self.url):
            initial_state_text = match1(html_content, r'__INITIAL_STATE__=(.*?);\(function\(\)')  # FIXME
            initial_state = json.loads(initial_state_text)
            ep_id = initial_state['epList'][0]['id']
            self.url = 'https://www.bilibili.com/bangumi/play/ep%s' % ep_id
            html_content = get_content(self.url, headers=self.bilibili_headers(referer=self.url))

        # redirect: s
        elif re.match(r'https?://(www\.)?bilibili\.com/s/(.+)', self.url):
            self.url = 'https://www.bilibili.com/%s' % match1(self.url, r'/s/(.+)')
            html_content = get_content(self.url, headers=self.bilibili_headers())

        # redirect: festival
        elif re.match(r'https?://(www\.)?bilibili\.com/festival/(.+)', self.url):
            self.url = 'https://www.bilibili.com/video/%s' % match1(self.url, r'bvid=([^&]+)')
            html_content = get_content(self.url, headers=self.bilibili_headers())

        # sort it out
        if re.match(r'https?://(www\.)?bilibili\.com/audio/au(\d+)', self.url):
            sort = 'audio'
        elif re.match(r'https?://(www\.)?bilibili\.com/bangumi/play/ep(\d+)', self.url):
            sort = 'bangumi'
        elif match1(html_content, r'<meta property="og:url" content="(https://www.bilibili.com/bangumi/play/[^"]+)"'):
            sort = 'bangumi'
        elif re.match(r'https?://live\.bilibili\.com/', self.url):
            sort = 'live'
        elif re.match(r'https?://vc\.bilibili\.com/video/(\d+)', self.url):
            sort = 'vc'
        elif re.match(r'https?://(www\.)?bilibili\.com/video/(av(\d+)|(bv(\S+))|(BV(\S+)))', self.url):
            sort = 'video'
        elif re.match(r'https?://h\.?bilibili\.com/(\d+)', self.url):
            sort = 'h'
        else:
            self.download_playlist_by_url(self.url, **kwargs)
            return

        # regular video
        if sort == 'video':
            initial_state_text = match1(html_content, r'__INITIAL_STATE__=(.*?);\(function\(\)')  # FIXME
            initial_state = json.loads(initial_state_text)

            playinfo_text = match1(html_content, r'__playinfo__=(.*?)</script><script>')  # FIXME
            playinfo = json.loads(playinfo_text) if playinfo_text else None
            playinfo = playinfo if playinfo and playinfo.get('code') == 0 else None

            html_content_ = get_content(self.url, headers=self.bilibili_headers(cookie='CURRENT_FNVAL=16'))
            playinfo_text_ = match1(html_content_, r'__playinfo__=(.*?)</script><script>')  # FIXME
            playinfo_ = json.loads(playinfo_text_) if playinfo_text_ else None
            playinfo_ = playinfo_ if playinfo_ and playinfo_.get('code') == 0 else None

            if 'videoData' in initial_state:
                # (standard video)

                # warn if cookies are not loaded
                if cookies is None:
                    log.w('You will need login cookies for 720p formats or above. (use --cookies to load cookies.txt.)')

                # warn if it is a multi-part video
                pn = initial_state['videoData']['videos']
                if pn > 1 and not kwargs.get('playlist'):
                    log.w('This is a multipart video. (use --playlist to download all parts.)')

                # set video title
                self.title = initial_state['videoData']['title']
                # refine title for a specific part, if it is a multi-part video
                p = int(match1(self.url, r'[\?&]p=(\d+)') or match1(self.url, r'/index_(\d+)') or
                        '1')  # use URL to decide p-number, not initial_state['p']
                if pn > 1:
                    part = initial_state['videoData']['pages'][p - 1]['part']
                    self.title = '%s (P%s. %s)' % (self.title, p, part)

                # construct playinfos
                avid = initial_state['aid']
                cid = initial_state['videoData']['pages'][p - 1]['cid']  # use p-number, not initial_state['videoData']['cid']
            else:
                # (festival video)

                # set video title
                self.title = initial_state['videoInfo']['title']

                # construct playinfos
                avid = initial_state['videoInfo']['aid']
                cid = initial_state['videoInfo']['cid']

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
            for qn in [120, 112, 80, 64, 32, 16]:
                # automatic format for durl: qn=0
                # for dash, qn does not matter
                if current_quality is None or qn < current_quality:
                    api_url = self.bilibili_api(avid, cid, qn=qn)
                    api_content = get_content(api_url, headers=self.bilibili_headers(referer=self.url))
                    api_playinfo = json.loads(api_content)
                    if api_playinfo['code'] == 0:  # success
                        playinfos.append(api_playinfo)
                    else:
                        message = api_playinfo['data']['message']
                if best_quality is None or qn <= best_quality:
                    api_url = self.bilibili_interface_api(cid, qn=qn)
                    api_content = get_content(api_url, headers=self.bilibili_headers(referer=self.url))
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
                        s = self.stream_qualities[video['id']]
                        format_id = f"dash-{s['id']}-{self.codecids[video['codecid']]}"  # prefix
                        container = 'mp4'  # enforce MP4 container
                        desc = s['desc'] + ' ' + video['codecs']
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
                                audio_size_cache[audio_quality] = self.url_size(audio_baseurl, headers=self.bilibili_headers(referer=self.url))
                            size += audio_size_cache[audio_quality]

                            self.dash_streams[format_id] = {'container': container, 'quality': desc,
                                                            'src': [[baseurl], [audio_baseurl]], 'size': size}
                        else:
                            self.dash_streams[format_id] = {'container': container, 'quality': desc,
                                                            'src': [[baseurl]], 'size': size}

            # get danmaku
            self.danmaku = get_content('https://comment.bilibili.com/%s.xml' % cid, headers=self.bilibili_headers(referer=self.url))

        # bangumi
        elif sort == 'bangumi':
            initial_state_text = match1(html_content, r'__INITIAL_STATE__=(.*?);\(function\(\)')  # FIXME
            initial_state = json.loads(initial_state_text)

            # warn if this bangumi has more than 1 video
            epn = len(initial_state['epList'])
            if epn > 1 and not kwargs.get('playlist'):
                log.w('This bangumi currently has %s videos. (use --playlist to download all videos.)' % epn)

            # set video title
            self.title = initial_state['h1Title']

            # construct playinfos
            ep_id = initial_state['epInfo']['id']
            avid = initial_state['epInfo']['aid']
            cid = initial_state['epInfo']['cid']
            playinfos = []
            api_url = self.bilibili_bangumi_api(avid, cid, ep_id)
            api_content = get_content(api_url, headers=self.bilibili_headers(referer=self.url))
            api_playinfo = json.loads(api_content)
            if api_playinfo['code'] == 0:  # success
                playinfos.append(api_playinfo)
            else:
                log.e(api_playinfo['message'])
                return
            current_quality = api_playinfo['result']['quality']
            # get alternative formats from API
            for fnval in [8, 16]:
                for qn in [120, 112, 80, 64, 32, 16]:
                    # automatic format for durl: qn=0
                    # for dash, qn does not matter
                    if qn != current_quality:
                        api_url = self.bilibili_bangumi_api(avid, cid, ep_id, qn=qn, fnval=fnval)
                        api_content = get_content(api_url, headers=self.bilibili_headers(referer=self.url))
                        api_playinfo = json.loads(api_content)
                        if api_playinfo['code'] == 0:  # success
                            playinfos.append(api_playinfo)

            for playinfo in playinfos:
                if 'durl' in playinfo['result']:
                    quality = playinfo['result']['quality']
                    format_id = self.stream_qualities[quality]['id']
                    container = self.stream_qualities[quality]['container'].lower()
                    desc = self.stream_qualities[quality]['desc']

                    src, size = [], 0
                    for durl in playinfo['result']['durl']:
                        src.append(durl['url'])
                        size += durl['size']
                    self.streams[format_id] = {'container': container, 'quality': desc, 'size': size, 'src': src}

                # DASH formats
                if 'dash' in playinfo['result']:
                    for video in playinfo['result']['dash']['video']:
                        # playinfo['result']['quality'] does not reflect the correct quality of DASH stream
                        quality = self.height_to_quality(video['height'], video['id'])  # convert height to quality code
                        s = self.stream_qualities[quality]
                        format_id = 'dash-' + s['id']  # prefix
                        container = 'mp4'  # enforce MP4 container
                        desc = s['desc']
                        audio_quality = s['audio_quality']
                        baseurl = video['baseUrl']
                        size = url_size(baseurl, headers=self.bilibili_headers(referer=self.url))

                        # find matching audio track
                        audio_baseurl = playinfo['result']['dash']['audio'][0]['baseUrl']
                        for audio in playinfo['result']['dash']['audio']:
                            if int(audio['id']) == audio_quality:
                                audio_baseurl = audio['baseUrl']
                                break
                        size += url_size(audio_baseurl, headers=self.bilibili_headers(referer=self.url))

                        self.dash_streams[format_id] = {'container': container, 'quality': desc,
                                                        'src': [[baseurl], [audio_baseurl]], 'size': size}

            # get danmaku
            self.danmaku = get_content('https://comment.bilibili.com/%s.xml' % cid, headers=self.bilibili_headers(referer=self.url))

        # vc video
        elif sort == 'vc':
            video_id = match1(self.url, r'https?://vc\.?bilibili\.com/video/(\d+)')
            api_url = self.bilibili_vc_api(video_id)
            api_content = get_content(api_url, headers=self.bilibili_headers())
            api_playinfo = json.loads(api_content)

            # set video title
            self.title = '%s (%s)' % (api_playinfo['data']['user']['name'], api_playinfo['data']['item']['id'])

            height = api_playinfo['data']['item']['height']
            quality = self.height_to_quality(height)  # convert height to quality code
            s = self.stream_qualities[quality]
            format_id = s['id']
            container = 'mp4'  # enforce MP4 container
            desc = s['desc']

            playurl = api_playinfo['data']['item']['video_playurl']
            size = int(api_playinfo['data']['item']['video_size'])

            self.streams[format_id] = {'container': container, 'quality': desc, 'size': size, 'src': [playurl]}

        # live
        elif sort == 'live':
            m = re.match(r'https?://live\.bilibili\.com/(\w+)', self.url)
            short_id = m.group(1)
            api_url = self.bilibili_live_room_init_api(short_id)
            api_content = get_content(api_url, headers=self.bilibili_headers())
            room_init_info = json.loads(api_content)

            room_id = room_init_info['data']['room_id']
            api_url = self.bilibili_live_room_info_api(room_id)
            api_content = get_content(api_url, headers=self.bilibili_headers())
            room_info = json.loads(api_content)

            # set video title
            self.title = room_info['data']['title'] + '.' + str(int(time.time()))

            api_url = self.bilibili_live_api(room_id)
            api_content = get_content(api_url, headers=self.bilibili_headers())
            video_info = json.loads(api_content)

            durls = video_info['data']['durl']
            playurl = durls[0]['url']
            container = 'flv'  # enforce FLV container
            self.streams['flv'] = {'container': container, 'quality': 'unknown',
                                   'size': 0, 'src': [playurl]}

        # audio
        elif sort == 'audio':
            m = re.match(r'https?://(?:www\.)?bilibili\.com/audio/au(\d+)', self.url)
            sid = m.group(1)
            api_url = self.bilibili_audio_info_api(sid)
            api_content = get_content(api_url, headers=self.bilibili_headers())
            song_info = json.loads(api_content)

            # set audio title
            self.title = song_info['data']['title']

            # get lyrics
            self.lyrics = get_content(song_info['data']['lyric'])

            api_url = self.bilibili_audio_api(sid)
            api_content = get_content(api_url, headers=self.bilibili_headers())
            audio_info = json.loads(api_content)

            playurl = audio_info['data']['cdns'][0]
            size = audio_info['data']['size']
            container = 'mp4'  # enforce MP4 container
            self.streams['mp4'] = {'container': container,
                                   'size': size, 'src': [playurl]}

        # h images
        elif sort == 'h':
            m = re.match(r'https?://h\.?bilibili\.com/(\d+)', self.url)
            doc_id = m.group(1)
            api_url = self.bilibili_h_api(doc_id)
            api_content = get_content(api_url, headers=self.bilibili_headers())
            h_info = json.loads(api_content)

            urls = []
            for pic in h_info['data']['item']['pictures']:
                img_src = pic['img_src']
                urls.append(img_src)
            size = urls_size(urls)

            self.title = doc_id
            container = 'jpg'  # enforce JPG container
            self.streams[container] = {'container': container,
                                       'size': size, 'src': urls}