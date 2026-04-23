def acfun_download(self, url, output_dir='.', merge=True, info_only=False, **kwargs):
        assert re.match(r'https?://[^\.]*\.*acfun\.[^\.]+/(\D|bangumi)/\D\D(\d+)', url)

        def getM3u8UrlFromCurrentVideoInfo(currentVideoInfo):
            if 'playInfos' in currentVideoInfo:
                return currentVideoInfo['playInfos'][0]['playUrls'][0]
            elif 'ksPlayJson' in currentVideoInfo:
                ksPlayJson = json.loads( currentVideoInfo['ksPlayJson'] )
                representation = ksPlayJson.get('adaptationSet')[0].get('representation')
                reps = []
                for one in representation:
                    reps.append( (one['width']* one['height'], one['url'], one['backupUrl']) )
                return max(reps)[1]


        if re.match(r'https?://[^\.]*\.*acfun\.[^\.]+/\D/\D\D(\d+)', url):
            html = get_content(url, headers=fake_headers)
            json_text = match1(html, r"(?s)videoInfo\s*=\s*(\{.*?\});")
            json_data = json.loads(json_text)
            vid = json_data.get('currentVideoInfo').get('id')
            up = json_data.get('user').get('name')
            title = json_data.get('title')
            video_list = json_data.get('videoList')
            if len(video_list) > 1:
                title += " - " + [p.get('title') for p in video_list if p.get('id') == vid][0]
            currentVideoInfo = json_data.get('currentVideoInfo')
            m3u8_url = getM3u8UrlFromCurrentVideoInfo(currentVideoInfo)
        elif re.match(r'https?://[^\.]*\.*acfun\.[^\.]+/bangumi/aa(\d+)', url):
            html = get_content(url, headers=fake_headers)
            tag_script = match1(html, r'<script>\s*window\.pageInfo([^<]+)</script>')
            json_text = tag_script[tag_script.find('{') : tag_script.find('};') + 1]
            json_data = json.loads(json_text)
            title = json_data['bangumiTitle'] + " " + json_data['episodeName'] + " " + json_data['title']
            vid = str(json_data['videoId'])
            up = "acfun"

            currentVideoInfo = json_data.get('currentVideoInfo')
            m3u8_url = getM3u8UrlFromCurrentVideoInfo(currentVideoInfo)

        else:
            raise NotImplementedError()

        assert title and m3u8_url
        title = unescape_html(title)
        title = escape_file_path(title)
        p_title = r1('active">([^<]+)', html)
        title = '%s (%s)' % (title, up)
        if p_title:
            title = '%s - %s' % (title, p_title)

        print_info(site_info, title, 'm3u8', float('inf'))
        if not info_only:
            download_url_ffmpeg(m3u8_url, title, 'mp4', output_dir=output_dir, merge=merge)