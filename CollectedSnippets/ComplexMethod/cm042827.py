def prepare(self, **kwargs):
        assert re.match(r'https?://[^\.]*\.*acfun\.[^\.]+/(\D|bangumi)/\D\D(\d+)', self.url)

        if re.match(r'https?://[^\.]*\.*acfun\.[^\.]+/\D/\D\D(\d+)', self.url):
            html = get_content(self.url, headers=fake_headers)
            json_text = match1(html, r"(?s)videoInfo\s*=\s*(\{.*?\});")
            json_data = json.loads(json_text)
            vid = json_data.get('currentVideoInfo').get('id')
            up = json_data.get('user').get('name')
            self.title = json_data.get('title')
            video_list = json_data.get('videoList')
            if len(video_list) > 1:
                self.title += " - " + [p.get('title') for p in video_list if p.get('id') == vid][0]
            currentVideoInfo = json_data.get('currentVideoInfo')

        elif re.match(r"https?://[^\.]*\.*acfun\.[^\.]+/bangumi/aa(\d+)", self.url):
            html = get_content(self.url, headers=fake_headers)
            tag_script = match1(html, r'<script>\s*window\.pageInfo([^<]+)</script>')
            json_text = tag_script[tag_script.find('{') : tag_script.find('};') + 1]
            json_data = json.loads(json_text)
            self.title = json_data['bangumiTitle'] + " " + json_data['episodeName'] + " " + json_data['title']
            vid = str(json_data['videoId'])
            up = "acfun"
            currentVideoInfo = json_data.get('currentVideoInfo')

        else:
            raise NotImplementedError()         

        if 'ksPlayJson' in currentVideoInfo:
            durationMillis = currentVideoInfo['durationMillis']
            ksPlayJson = ksPlayJson = json.loads( currentVideoInfo['ksPlayJson'] )
            representation = ksPlayJson.get('adaptationSet')[0].get('representation')
            stream_list = representation

        for stream in stream_list:
            m3u8_url = stream["url"]
            size = durationMillis * stream["avgBitrate"] / 8
            # size = float('inf')
            container = 'mp4'
            stream_id = stream["qualityLabel"]
            quality = stream["qualityType"]

            stream_data = dict(src=m3u8_url, size=size, container=container, quality=quality)
            self.streams[stream_id] = stream_data

        assert self.title and m3u8_url
        self.title = unescape_html(self.title)
        self.title = escape_file_path(self.title)
        p_title = r1('active">([^<]+)', html)
        self.title = '%s (%s)' % (self.title, up)
        if p_title:
            self.title = '%s - %s' % (self.title, p_title)