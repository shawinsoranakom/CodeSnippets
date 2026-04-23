def prepare(self, **kwargs):
        if self.url:
            self.vid = self.get_vid_from_url(self.url)
        content_info = get_content(self.info_endpoint.format(video_id=self.vid))
        log.d(content_info)
        content_info = loads(content_info)
        self.title = content_info['data']['info']['videoName']

        content_player = get_content(self.player_endpoint.format(did=self.did, video_id=self.vid, tk2=self.tk2()))
        log.d(content_player)
        content_player = loads(content_player)
        pm2 = content_player['data']['atc']['pm2']

        content_source = get_content(self.source_endpoint.format(video_id=self.vid, tk2=self.tk2(), pm2=pm2))
        log.d(content_source)
        content_source = loads(content_source)
        domain = content_source['data']['stream_domain'][0]

        # stream_available = [i['name'] for i in content['data']['stream']]
        stream_available = {}
        for i in content_source['data']['stream']:
            stream_available[i['name']] = i['url']

        for s in self.stream_types:
            if s['video_profile'] in stream_available.keys():
                quality_id = self.id_dic[s['video_profile']]
                url = stream_available[s['video_profile']]
                if url is None or url == '':
                    # skip invalid profile with empty url
                    continue
                url = domain + re.sub(r'(\&arange\=\d+)', '', url)  # Un-Hum
                m3u8_url, m3u8_size, segment_list_this = self.get_mgtv_real_url(url)

                stream_fileid_list = []
                for i in segment_list_this:
                    stream_fileid_list.append(os.path.basename(i).split('.')[0])

                # make pieces
                pieces = []
                for i in zip(stream_fileid_list, segment_list_this):
                    pieces.append({'fileid': i[0], 'segs': i[1], })

                    self.streams[quality_id] = {
                        'container': s['container'],
                        'video_profile': s['video_profile'],
                        'size': m3u8_size,
                        'pieces': pieces,
                        'm3u8_url': m3u8_url
                    }

                if not kwargs['info_only']:
                    self.streams[quality_id]['src'] = segment_list_this