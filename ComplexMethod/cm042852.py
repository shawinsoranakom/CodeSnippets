def kugou_download_playlist(url, output_dir='.', merge=True, info_only=False, **kwargs):
    urls = []

    # download music leaderboard
    # sample: http://www.kugou.com/yy/html/rank.html
    if url.lower().find('rank') != -1:
        html = get_html(url)
        pattern = re.compile('<a href="(http://.*?)" data-active=')
        res = pattern.findall(html)
        for song in res:
            res = get_html(song)
            pattern_url = re.compile(r'"hash":"(\w+)".*"album_id":(\d)+')
            hash_val, album_id = res = pattern_url.findall(res)[0]
            if not album_id:
                album_id = 123
            urls.append('http://www.kugou.com/song/#hash=%s&album_id=%s' % (hash_val, album_id))

    # download album
    # album sample:   http://www.kugou.com/yy/album/single/1645030.html
    elif url.lower().find('album') != -1:
        html = get_html(url)
        pattern = re.compile(r'var data=(\[.*?\]);')
        res = pattern.findall(html)[0]
        for v in json.loads(res):
            urls.append('http://www.kugou.com/song/#hash=%s&album_id=%s' % (v['hash'], v['album_id']))

    # download the playlist        
    # playlist sample:http://www.kugou.com/yy/special/single/487279.html
    else:
        html = get_html(url)
        pattern = re.compile(r'data="(\w+)\|(\d+)"')
        for v in pattern.findall(html):
            urls.append('http://www.kugou.com/song/#hash=%s&album_id=%s' % (v[0], v[1]))
            print('http://www.kugou.com/song/#hash=%s&album_id=%s' % (v[0], v[1]))

    # download the list by hash
    for url in urls:
        kugou_download_by_hash(url, output_dir, merge, info_only)