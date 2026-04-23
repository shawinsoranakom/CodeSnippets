def sndcd_download(url, output_dir='.', merge=True, info_only=False, **kwargs):
    client_id = get_sndcd_apikey()

    r_info = get_resource_info(url, client_id)

    for info in r_info:
        title = info['title']
        metadata = info.get('publisher_metadata')

        transcodings = info['media']['transcodings']
        sq = [i for i in transcodings if i['quality'] == 'sq']
        hq = [i for i in transcodings if i['quality'] == 'hq']
        # source url
        surl = sq[0] if hq == [] else hq[0]
        surl = surl['url']

        uri = surl + '?client_id=' + client_id
        r = get_content(uri)
        surl = json.loads(r)['url']

        m3u8 = get_content(surl)
        # url list
        urll = re.findall(r'http.*?(?=\n)', m3u8)

        size = urls_size(urll)
        print_info(site_info, title, 'audio/mpeg', size)
        print(end='', flush=True)

        if not info_only:
            download_urls(urll, title=title, ext='mp3', total_size=size, output_dir=output_dir, merge=True)