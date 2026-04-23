def embed_download(url, output_dir = '.', merge = True, info_only = False, **kwargs):
    content = get_content(url, headers=fake_headers)
    found = False
    title = match1(content, '<title>([^<>]+)</title>')

    vids = matchall(content, youku_embed_patterns)
    for vid in set(vids):
        found = True
        youku_download_by_vid(vid, title=title, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)

    vids = matchall(content, tudou_embed_patterns)
    for vid in set(vids):
        found = True
        tudou_download_by_id(vid, title=title, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)

    vids = matchall(content, iqiyi_embed_patterns)
    for vid in vids:
        found = True
        iqiyi_download_by_vid((vid[1], vid[0]), title=title, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)

    urls = matchall(content, netease_embed_patterns)
    for url in urls:
        found = True
        netease_download(url, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)

    urls = matchall(content, vimeo_embed_patters)
    for url in urls:
        found = True
        vimeo_download_by_id(url, title=title, output_dir=output_dir, merge=merge, info_only=info_only, referer=url, **kwargs)

    urls = matchall(content, dailymotion_embed_patterns)
    for url in urls:
        found = True
        dailymotion_download(url, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)

    aids = matchall(content, bilibili_embed_patterns)
    for aid in aids:
        found = True
        url = 'http://www.bilibili.com/video/av%s/' % aid
        bilibili_download(url, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)

    iqiyi_urls = matchall(content, iqiyi_patterns)
    for url in iqiyi_urls:
        found = True
        iqiyi.download(url, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)

    bokecc_metas = matchall(content, bokecc_patterns)
    for meta in bokecc_metas:
        found = True
        bokecc.bokecc_download_by_id(meta[1], output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)

    if found:
        return True

    # Try harder, check all iframes
    if 'recur_lv' not in kwargs or kwargs['recur_lv'] < recur_limit:
        r = kwargs.get('recur_lv')
        if r is None:
            r = 1
        else:
            r += 1
        iframes = matchall(content, [r'<iframe.+?src=(?:\"|\')(.*?)(?:\"|\')'])
        for iframe in iframes:
            if not iframe.startswith('http'):
                src = urllib.parse.urljoin(url, iframe)
            else:
                src = iframe
            found = embed_download(src, output_dir=output_dir, merge=merge, info_only=info_only, recur_lv=r, **kwargs)
            if found:
                return True

    if not found and 'recur_lv' not in kwargs:
        raise NotImplementedError(url)
    else:
        return found