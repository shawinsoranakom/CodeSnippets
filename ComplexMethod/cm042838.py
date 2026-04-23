def tudou_download(url, output_dir = '.', merge = True, info_only = False, **kwargs):
    if 'acfun.tudou.com' in url:  #wrong way!
        url = url.replace('acfun.tudou.com', 'www.acfun.tv')
        you_get.extractors.acfun.acfun_download(url, output_dir,
                                               merge,
                                               info_only)
        return  #throw you back

    # Embedded player
    id = r1(r'http://www.tudou.com/v/([^/]+)/', url)
    if id:
        return tudou_download_by_id(id, title="", info_only=info_only)

    html = get_content(url)

    try:
        title = r1(r'\Wkw\s*[:=]\s*[\'\"]([^\n]+?)\'\s*\n', html).replace("\\'", "\'")
        assert title
        title = unescape_html(title)
    except AttributeError:
        title = match1(html, r'id=\"subtitle\"\s*title\s*=\s*\"([^\"]+)\"')
        if title is None:
            title = ''

    vcode = r1(r'vcode\s*[:=]\s*\'([^\']+)\'', html)
    if vcode is None:
        vcode = match1(html, r'viden\s*[:=]\s*\"([\w+/=]+)\"')
    if vcode:
        from .youku import youku_download_by_vid
        return youku_download_by_vid(vcode, title=title, output_dir=output_dir, merge=merge, info_only=info_only, src='tudou', **kwargs)

    iid = r1(r'iid\s*[:=]\s*(\d+)', html)
    if not iid:
        return tudou_download_playlist(url, output_dir, merge, info_only)

    tudou_download_by_iid(iid, title, output_dir = output_dir, merge = merge, info_only = info_only)