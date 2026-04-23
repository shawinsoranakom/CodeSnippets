def download_playlist_by_url(self, url, **kwargs):
        self.url = url
        kwargs['playlist'] = True

        html_content = get_content(self.url, headers=self.bilibili_headers(referer=self.url))

        # sort it out
        if re.match(r'https?://(www\.)?bilibili\.com/bangumi/play/ep(\d+)', self.url):
            sort = 'bangumi'
        elif match1(html_content, r'<meta property="og:url" content="(https://www.bilibili.com/bangumi/play/[^"]+)"'):
            sort = 'bangumi'
        elif re.match(r'https?://(www\.)?bilibili\.com/bangumi/media/md(\d+)', self.url) or \
            re.match(r'https?://bangumi\.bilibili\.com/anime/(\d+)', self.url):
            sort = 'bangumi_md'
        elif re.match(r'https?://(www\.)?bilibili\.com/video/(av(\d+)|bv(\S+)|BV(\S+))', self.url):
            sort = 'video'
        elif re.match(r'https?://space\.?bilibili\.com/(\d+)/channel/detail\?.*cid=(\d+)', self.url):
            sort = 'space_channel'
        elif re.match(r'https?://space\.?bilibili\.com/(\d+)/channel/seriesdetail\?.*sid=(\d+)', self.url):
            sort = 'space_channel_series'
        elif re.match(r'https?://space\.?bilibili\.com/(\d+)/channel/collectiondetail\?.*sid=(\d+)', self.url):
            sort = 'space_channel_collection'
        elif re.match(r'https?://space\.?bilibili\.com/(\d+)/favlist\?.*fid=(\d+)', self.url):
            sort = 'space_favlist'
        elif re.match(r'https?://space\.?bilibili\.com/(\d+)/video', self.url):
            sort = 'space_video'
        elif re.match(r'https?://(www\.)?bilibili\.com/audio/am(\d+)', self.url):
            sort = 'audio_menu'
        else:
            log.e('[Error] Unsupported URL pattern.')
            exit(1)

        # regular video
        if sort == 'video':
            initial_state_text = match1(html_content, r'__INITIAL_STATE__=(.*?);\(function\(\)')  # FIXME
            initial_state = json.loads(initial_state_text)
            aid = initial_state['videoData']['aid']
            pn = initial_state['videoData']['videos']

            if pn == len(initial_state['videoData']['pages']):
                # non-interative video
                for pi in range(1, pn + 1):
                     purl = 'https://www.bilibili.com/video/av%s?p=%s' % (aid, pi)
                     self.__class__().download_by_url(purl, **kwargs)

            else:
                # interative video
                search_node_list = []
                download_cid_set = set([initial_state['videoData']['cid']])
                params = {
                        'id': 'cid:{}'.format(initial_state['videoData']['cid']),
                        'aid': str(aid)
                }
                urlcontent = get_content('https://api.bilibili.com/x/player.so?'+parse.urlencode(params), headers=self.bilibili_headers(referer='https://www.bilibili.com/video/av{}'.format(aid)))
                graph_version = json.loads(urlcontent[urlcontent.find('<interaction>')+13:urlcontent.find('</interaction>')])['graph_version']
                params = {
                    'aid': str(aid),
                    'graph_version': graph_version,
                    'platform': 'pc',
                    'portal': 0,
                    'screen': 0,
                }
                node_info = json.loads(get_content('https://api.bilibili.com/x/stein/nodeinfo?'+parse.urlencode(params)))

                playinfo_text = match1(html_content, r'__playinfo__=(.*?)</script><script>')  # FIXME
                playinfo = json.loads(playinfo_text) if playinfo_text else None

                html_content_ = get_content(self.url, headers=self.bilibili_headers(cookie='CURRENT_FNVAL=16'))
                playinfo_text_ = match1(html_content_, r'__playinfo__=(.*?)</script><script>')  # FIXME
                playinfo_ = json.loads(playinfo_text_) if playinfo_text_ else None

                self.prepare_by_cid(aid, initial_state['videoData']['cid'], initial_state['videoData']['title'] + ('P{}. {}'.format(1, node_info['data']['title'])),html_content,playinfo,playinfo_,url)
                self.extract(**kwargs)
                self.download(**kwargs)
                for choice in node_info['data']['edges']['choices']:
                    search_node_list.append(choice['node_id'])
                    if not choice['cid'] in download_cid_set:
                        download_cid_set.add(choice['cid'])
                        self.prepare_by_cid(aid,choice['cid'],initial_state['videoData']['title']+('P{}. {}'.format(len(download_cid_set),choice['option'])),html_content,playinfo,playinfo_,url)
                        self.extract(**kwargs)
                        self.download(**kwargs)
                while len(search_node_list)>0:
                    node_id = search_node_list.pop(0)
                    params.update({'node_id':node_id})
                    node_info = json.loads(get_content('https://api.bilibili.com/x/stein/nodeinfo?'+parse.urlencode(params)))
                    if node_info['data'].__contains__('edges'):
                        for choice in node_info['data']['edges']['choices']:
                            search_node_list.append(choice['node_id'])
                            if not choice['cid'] in download_cid_set:
                                download_cid_set.add(choice['cid'])
                                self.prepare_by_cid(aid,choice['cid'],initial_state['videoData']['title']+('P{}. {}'.format(len(download_cid_set),choice['option'])),html_content,playinfo,playinfo_,url)
                                try:
                                    self.streams_sorted = [dict([('id', stream_type['id'])] + list(self.streams[stream_type['id']].items())) for stream_type in self.__class__.stream_types if stream_type['id'] in self.streams]
                                except:
                                    self.streams_sorted = [dict([('itag', stream_type['itag'])] + list(self.streams[stream_type['itag']].items())) for stream_type in self.__class__.stream_types if stream_type['itag'] in self.streams]
                                self.extract(**kwargs)
                                self.download(**kwargs)

        elif sort == 'bangumi':
            initial_state_text = match1(html_content, r'__INITIAL_STATE__=(.*?);\(function\(\)')  # FIXME
            initial_state = json.loads(initial_state_text)
            epn, i = len(initial_state['epList']), 0
            for ep in initial_state['epList']:
                i += 1; log.w('Extracting %s of %s videos ...' % (i, epn))
                ep_id = ep['id']
                epurl = 'https://www.bilibili.com/bangumi/play/ep%s/' % ep_id
                self.__class__().download_by_url(epurl, **kwargs)

        elif sort == 'bangumi_md':
            initial_state_text = match1(html_content, r'__INITIAL_STATE__=(.*?);\(function\(\)')  # FIXME
            initial_state = json.loads(initial_state_text)
            epn, i = len(initial_state['mediaInfo']['episodes']), 0
            for ep in initial_state['mediaInfo']['episodes']:
                i += 1; log.w('Extracting %s of %s videos ...' % (i, epn))
                ep_id = ep['ep_id']
                epurl = 'https://www.bilibili.com/bangumi/play/ep%s/' % ep_id
                self.__class__().download_by_url(epurl, **kwargs)

        elif sort == 'space_channel':
            m = re.match(r'https?://space\.?bilibili\.com/(\d+)/channel/detail\?.*cid=(\d+)', self.url)
            mid, cid = m.group(1), m.group(2)
            api_url = self.bilibili_space_channel_api(mid, cid)
            api_content = get_content(api_url, headers=self.bilibili_headers(referer=self.url))
            channel_info = json.loads(api_content)
            # TBD: channel of more than 100 videos

            epn, i = len(channel_info['data']['list']['archives']), 0
            for video in channel_info['data']['list']['archives']:
                i += 1; log.w('Extracting %s of %s videos ...' % (i, epn))
                url = 'https://www.bilibili.com/video/av%s' % video['aid']
                self.__class__().download_playlist_by_url(url, **kwargs)

        elif sort == 'space_channel_series':
            m = re.match(r'https?://space\.?bilibili\.com/(\d+)/channel/seriesdetail\?.*sid=(\d+)', self.url)
            mid, sid = m.group(1), m.group(2)
            pn = 1
            video_list = []
            while True:
                api_url = self.bilibili_series_archives_api(mid, sid, pn)
                api_content = get_content(api_url, headers=self.bilibili_headers(referer=self.url))
                archives_info = json.loads(api_content)
                video_list.extend(archives_info['data']['archives'])
                if len(video_list) < archives_info['data']['page']['total'] and len(archives_info['data']['archives']) > 0:
                    pn += 1
                else:
                    break

            epn, i = len(video_list), 0
            for video in video_list:
                i += 1; log.w('Extracting %s of %s videos ...' % (i, epn))
                url = 'https://www.bilibili.com/video/av%s' % video['aid']
                self.__class__().download_playlist_by_url(url, **kwargs)

        elif sort == 'space_channel_collection':
            m = re.match(r'https?://space\.?bilibili\.com/(\d+)/channel/collectiondetail\?.*sid=(\d+)', self.url)
            mid, sid = m.group(1), m.group(2)
            pn = 1
            video_list = []
            while True:
                api_url = self.bilibili_space_collection_api(mid, sid, pn)
                api_content = get_content(api_url, headers=self.bilibili_headers(referer=self.url))
                archives_info = json.loads(api_content)
                video_list.extend(archives_info['data']['archives'])
                if len(video_list) < archives_info['data']['page']['total'] and len(archives_info['data']['archives']) > 0:
                    pn += 1
                else:
                    break

            epn, i = len(video_list), 0
            for video in video_list:
                i += 1; log.w('Extracting %s of %s videos ...' % (i, epn))
                url = 'https://www.bilibili.com/video/av%s' % video['aid']
                self.__class__().download_playlist_by_url(url, **kwargs)

        elif sort == 'space_favlist':
            m = re.match(r'https?://space\.?bilibili\.com/(\d+)/favlist\?.*fid=(\d+)', self.url)
            vmid, fid = m.group(1), m.group(2)
            api_url = self.bilibili_space_favlist_api(fid)
            api_content = get_content(api_url, headers=self.bilibili_headers(referer=self.url))
            favlist_info = json.loads(api_content)
            pc = favlist_info['data']['info']['media_count'] // len(favlist_info['data']['medias'])
            if favlist_info['data']['info']['media_count'] % len(favlist_info['data']['medias']) != 0:
                pc += 1
            for pn in range(1, pc + 1):
                log.w('Extracting %s of %s pages ...' % (pn, pc))
                api_url = self.bilibili_space_favlist_api(fid, pn=pn)
                api_content = get_content(api_url, headers=self.bilibili_headers(referer=self.url))
                favlist_info = json.loads(api_content)

                epn, i = len(favlist_info['data']['medias']), 0
                for video in favlist_info['data']['medias']:
                    i += 1; log.w('Extracting %s of %s videos ...' % (i, epn))
                    url = 'https://www.bilibili.com/video/av%s' % video['id']
                    self.__class__().download_playlist_by_url(url, **kwargs)

        elif sort == 'space_video':
            m = re.match(r'https?://space\.?bilibili\.com/(\d+)/video', self.url)
            mid = m.group(1)
            api_url = self.bilibili_space_video_api(mid)
            api_content = get_content(api_url, headers=self.bilibili_headers())
            videos_info = json.loads(api_content)
            # pc = videos_info['data']['page']['count'] // videos_info['data']['page']['ps']
            pc = math.ceil(videos_info['data']['page']['count'] / videos_info['data']['page']['ps'])

            for pn in range(1, pc + 1):
                api_url = self.bilibili_space_video_api(mid, pn=pn)
                api_content = get_content(api_url, headers=self.bilibili_headers())
                videos_info = json.loads(api_content)

                epn, i = len(videos_info['data']['list']['vlist']), 0
                for video in videos_info['data']['list']['vlist']:
                    i += 1; log.w('Extracting %s of %s videos ...' % (i, epn))
                    url = 'https://www.bilibili.com/video/av%s' % video['aid']
                    self.__class__().download_playlist_by_url(url, **kwargs)

        elif sort == 'audio_menu':
            m = re.match(r'https?://(?:www\.)?bilibili\.com/audio/am(\d+)', self.url)
            sid = m.group(1)
            #api_url = self.bilibili_audio_menu_info_api(sid)
            #api_content = get_content(api_url, headers=self.bilibili_headers())
            #menu_info = json.loads(api_content)
            api_url = self.bilibili_audio_menu_song_api(sid)
            api_content = get_content(api_url, headers=self.bilibili_headers())
            menusong_info = json.loads(api_content)
            epn, i = len(menusong_info['data']['data']), 0
            for song in menusong_info['data']['data']:
                i += 1; log.w('Extracting %s of %s songs ...' % (i, epn))
                url = 'https://www.bilibili.com/audio/au%s' % song['id']
                self.__class__().download_by_url(url, **kwargs)