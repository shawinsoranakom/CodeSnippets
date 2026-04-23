def qq_download_by_vid(vid, title, output_dir='.', merge=True, info_only=False):

    # http://v.sports.qq.com/#/cover/t0fqsm1y83r8v5j/a0026nvw5jr https://v.qq.com/x/cover/t0fqsm1y83r8v5j/a0026nvw5jr.html
    video_json = None
    platforms = [4100201, 11]
    for platform in platforms:
        info_api = 'http://vv.video.qq.com/getinfo?otype=json&appver=3.2.19.333&platform={}&defnpayver=1&defn=shd&vid={}'.format(platform, vid)
        info = get_content(info_api, headers)
        video_json = json.loads(match1(info, r'QZOutputJson=(.*)')[:-1])
        if not video_json.get('msg')=='cannot play outside':
            break
    fn_pre = video_json['vl']['vi'][0]['lnk']
    title = video_json['vl']['vi'][0]['ti']
    host = video_json['vl']['vi'][0]['ul']['ui'][0]['url']
    seg_cnt = fc_cnt = video_json['vl']['vi'][0]['cl']['fc']

    filename = video_json['vl']['vi'][0]['fn']
    if seg_cnt == 0:
        seg_cnt = 1
    else:
        fn_pre, magic_str, video_type = filename.split('.')

    part_urls= []
    total_size = 0
    ext = None
    for part in range(1, seg_cnt+1):
        if fc_cnt == 0:
            # fix json parsing error
            # example:https://v.qq.com/x/page/w0674l9yrrh.html
            part_format_id = video_json['vl']['vi'][0]['cl']['keyid'].split('.')[-1]
        else:
            part_format_id = video_json['vl']['vi'][0]['cl']['ci'][part - 1]['keyid'].split('.')[1]
            filename = '.'.join([fn_pre, magic_str, str(part), video_type])

        key_api = "http://vv.video.qq.com/getkey?otype=json&platform=11&format={}&vid={}&filename={}&appver=3.2.19.333".format(part_format_id, vid, filename)
        part_info = get_content(key_api, headers)
        key_json = json.loads(match1(part_info, r'QZOutputJson=(.*)')[:-1])
        if key_json.get('key') is None:
            vkey = video_json['vl']['vi'][0]['fvkey']
            url = '{}{}?vkey={}'.format(video_json['vl']['vi'][0]['ul']['ui'][0]['url'], fn_pre + '.mp4', vkey)
        else:
            vkey = key_json['key']
            url = '{}{}?vkey={}'.format(host, filename, vkey)
        if not vkey:
            if part == 1:
                log.wtf(key_json['msg'])
            else:
                log.w(key_json['msg'])
            break
        if key_json.get('filename') is None:
            log.w(key_json['msg'])
            break

        part_urls.append(url)
        _, ext, size = url_info(url)
        total_size += size

    print_info(site_info, title, ext, total_size)
    if not info_only:
        download_urls(part_urls, title, ext, total_size, output_dir=output_dir, merge=merge)