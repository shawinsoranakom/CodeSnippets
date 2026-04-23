def qq_download(url, output_dir='.', merge=True, info_only=False, **kwargs):
    """"""

    if re.match(r'https?://(m\.)?egame.qq.com/', url):
        from . import qq_egame
        qq_egame.qq_egame_download(url, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)
        return

    if 'kg.qq.com' in url or 'kg2.qq.com' in url:
        shareid = url.split('?s=')[-1]
        caption = kwargs['caption']
        kg_qq_download_by_shareid(shareid, output_dir=output_dir, info_only=info_only, caption=caption)
        return

    if 'live.qq.com' in url:
        if 'live.qq.com/video/v' in url:
            qie_video_download(url, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)
        else:
            qieDownload(url, output_dir=output_dir, merge=merge, info_only=info_only)
        return

    if 'mp.weixin.qq.com/s' in url:
        content = get_content(url, headers)
        vids = matchall(content, [r'[?;]vid=(\w+)'])
        for vid in vids:
            qq_download_by_vid(vid, vid, output_dir, merge, info_only)
        return

    if 'kuaibao.qq.com/s/' in url:
        # https://kuaibao.qq.com/s/20180521V0Z9MH00
        nid = match1(url, r'/s/([^/&?#]+)')
        content = get_content('https://kuaibao.qq.com/getVideoRelate?id=' + nid)
        info_json = json.loads(content)
        vid=info_json['videoinfo']['vid']
        title=info_json['videoinfo']['title']
    elif 'kuaibao.qq.com' in url or re.match(r'http://daxue.qq.com/content/content/id/\d+', url):
        # http://daxue.qq.com/content/content/id/2321
        content = get_content(url, headers)
        vid = match1(content, r'vid\s*=\s*"\s*([^"]+)"')
        title = match1(content, r'title">([^"]+)</p>')
        title = title.strip() if title else vid
    elif 'iframe/player.html' in url:
        vid = match1(url, r'\bvid=(\w+)')
        # for embedded URLs; don't know what the title is
        title = vid
    elif 'view.inews.qq.com' in url:
        # view.inews.qq.com/a/20180521V0Z9MH00
        content = get_content(url, headers)
        vid = match1(content, r'"vid":"(\w+)"')
        title = match1(content, r'"title":"(\w+)"')
    else:
        content = get_content(url, headers)
        #vid = parse_qs(urlparse(url).query).get('vid') #for links specified vid  like http://v.qq.com/cover/p/ps6mnfqyrfo7es3.html?vid=q0181hpdvo5
        rurl = match1(content, r'<link.*?rel\s*=\s*"canonical".*?href\s*="(.+?)".*?>') #https://v.qq.com/x/cover/9hpjiv5fhiyn86u/t0522x58xma.html
        vid = ""
        if rurl:
            vid = rurl.split('/')[-1].split('.')[0]
            # https://v.qq.com/x/page/d0552xbadkl.html https://y.qq.com/n/yqq/mv/v/g00268vlkzy.html
            if vid == "undefined" or vid == "index":
                vid = ""
        vid = vid if vid else url.split('/')[-1].split('.')[0] #https://v.qq.com/x/cover/ps6mnfqyrfo7es3/q0181hpdvo5.html?
        vid = vid if vid else match1(content, r'vid"*\s*:\s*"\s*([^"]+)"') #general fallback
        if not vid:
            vid = match1(content, r'id"*\s*:\s*"(.+?)"')
        title = match1(content,r'<a.*?id\s*=\s*"%s".*?title\s*=\s*"(.+?)".*?>'%vid)
        title = match1(content, r'title">([^"]+)</p>') if not title else title
        title = match1(content, r'"title":"([^"]+)"') if not title else title
        title = vid if not title else title #general fallback


    qq_download_by_vid(vid, title, output_dir, merge, info_only)