def baidu_download(url, output_dir='.', stream_type=None, merge=True, info_only=False, **kwargs):

    if re.match(r'https?://pan.baidu.com', url):
        real_url, title, ext, size = baidu_pan_download(url)
        print_info('BaiduPan', title, ext, size)
        if not info_only:
            print('Hold on...')
            time.sleep(5)
            download_urls([real_url], title, ext, size,
                          output_dir, url, merge=merge, faker=True)
    elif re.match(r'https?://music.baidu.com/album/\d+', url):
        id = r1(r'https?://music.baidu.com/album/(\d+)', url)
        baidu_download_album(id, output_dir, merge, info_only)

    elif re.match(r'https?://music.baidu.com/song/\d+', url):
        id = r1(r'https?://music.baidu.com/song/(\d+)', url)
        baidu_download_song(id, output_dir, merge, info_only)

    elif re.match('https?://tieba.baidu.com/', url):
        try:
            # embedded videos
            embed_download(url, output_dir, merge=merge, info_only=info_only, **kwargs)
        except:
            # images
            html = get_html(url)
            title = r1(r'title:"([^"]+)"', html)

            vhsrc = re.findall(r'"BDE_Image"[^>]+src="([^"]+\.mp4)"', html) or \
                re.findall(r'vhsrc="([^"]+)"', html)
            if len(vhsrc) > 0:
                ext = 'mp4'
                size = url_size(vhsrc[0])
                print_info(site_info, title, ext, size)
                if not info_only:
                    download_urls(vhsrc, title, ext, size,
                                  output_dir=output_dir, merge=False)

            items = re.findall(
                r'//tiebapic.baidu.com/forum/w[^"]+/([^/"]+)', html)
            urls = ['http://tiebapic.baidu.com/forum/pic/item/' + i
                    for i in set(items)]

            # handle albums
            kw = r1(r'kw=([^&]+)', html) or r1(r"kw:'([^']+)'", html)
            tid = r1(r'tid=(\d+)', html) or r1(r"tid:'([^']+)'", html)
            album_url = 'http://tieba.baidu.com/photo/g/bw/picture/list?kw=%s&tid=%s&pe=%s' % (kw, tid, 1000)
            album_info = json.loads(get_content(album_url))
            for i in album_info['data']['pic_list']:
                urls.append(
                    'http://tiebapic.baidu.com/forum/pic/item/' + i['pic_id'] + '.jpg')

            ext = 'jpg'
            size = float('Inf')
            print_info(site_info, title, ext, size)

            if not info_only:
                download_urls(urls, title, ext, size,
                              output_dir=output_dir, merge=False)