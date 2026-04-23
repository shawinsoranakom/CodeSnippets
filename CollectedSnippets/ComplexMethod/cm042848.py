def w56_download_by_id(id, title = None, output_dir = '.', merge = True, info_only = False):
    content = json.loads(get_html('http://vxml.56.com/json/%s/?src=site' % id))
    info = content['info']
    title = title or info['Subject']
    assert title
    hd = info['hd']
    assert hd in (0, 1, 2)
    hd_types = [['normal', 'qvga'], ['clear', 'vga'], ['super', 'wvga']][hd]
    files = [x for x in info['rfiles'] if x['type'] in hd_types]
    assert len(files) == 1
    size = int(files[0]['filesize'])
    url = files[0]['url'] + '&prod=56'
    ext = 'mp4'

    print_info(site_info, title, ext, size)
    if not info_only:
        download_urls([url], title, ext, size, output_dir = output_dir, merge = merge)