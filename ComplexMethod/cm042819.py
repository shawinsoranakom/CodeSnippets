def youku_download_playlist_by_url(url, **kwargs):
    video_page_pt = 'https?://v.youku.com/v_show/id_([A-Za-z0-9=]+)'
    js_cb_pt = r'\(({.+})\)'
    if re.match(video_page_pt, url):
        youku_obj = Youku()
        youku_obj.url = url
        youku_obj.prepare(**kwargs)
        total_episode = None
        try:
            total_episode = youku_obj.api_data['show']['episode_total']
        except KeyError:
            log.wtf('Cannot get total_episode for {}'.format(url))
        next_vid = youku_obj.vid
        for _ in range(total_episode):
            this_extractor = Youku()
            this_extractor.download_by_vid(next_vid, keep_obj=True, **kwargs)
            next_vid = this_extractor.video_next['encodevid']
        '''
        if youku_obj.video_list is None:
            log.wtf('Cannot find video list for {}'.format(url))
        else:
            vid_list = [v['encodevid'] for v in youku_obj.video_list]
            for v in vid_list:
                Youku().download_by_vid(v, **kwargs)
        '''

    elif re.match('https?://list.youku.com/show/id_', url):
        # http://list.youku.com/show/id_z2ae8ee1c837b11e18195.html
        # official playlist
        page = get_content(url)
        show_id = re.search(r'showid:"(\d+)"', page).group(1)
        ep = 'http://list.youku.com/show/module?id={}&tab=showInfo&callback=jQuery'.format(show_id)
        xhr_page = get_content(ep).replace(r'\/', '/').replace(r'\"', '"')
        video_url = re.search(r'(v.youku.com/v_show/id_(?:[A-Za-z0-9=]+)\.html)', xhr_page).group(1)
        youku_download_playlist_by_url('http://'+video_url, **kwargs)
        return
    elif re.match(r'https?://list.youku.com/albumlist/show/id_(\d+)\.html', url):
        # http://list.youku.com/albumlist/show/id_2336634.html
        # UGC playlist
        list_id = re.search(r'https?://list.youku.com/albumlist/show/id_(\d+)\.html', url).group(1)
        ep = 'http://list.youku.com/albumlist/items?id={}&page={}&size=20&ascending=1&callback=tuijsonp6'

        first_u = ep.format(list_id, 1)
        xhr_page = get_content(first_u)
        json_data = json.loads(re.search(js_cb_pt, xhr_page).group(1))
        video_cnt = json_data['data']['total']
        xhr_html = json_data['html']
        v_urls = re.findall(r'(v.youku.com/v_show/id_(?:[A-Za-z0-9=]+)\.html)', xhr_html)

        if video_cnt > 20:
            req_cnt = video_cnt // 20
            for i in range(2, req_cnt+2):
                req_u = ep.format(list_id, i)
                xhr_page = get_content(req_u)
                json_data = json.loads(re.search(js_cb_pt, xhr_page).group(1).replace(r'\/', '/'))
                xhr_html = json_data['html']
                page_videos = re.findall(r'(v.youku.com/v_show/id_(?:[A-Za-z0-9=]+)\.html)', xhr_html)
                v_urls.extend(page_videos)
        for u in v_urls[0::2]:
            url = 'http://' + u
            Youku().download_by_url(url, **kwargs)
        return