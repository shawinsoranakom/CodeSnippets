def netease_cloud_music_download(url, output_dir='.', merge=True, info_only=False, **kwargs):
    rid = match1(url, r'\Wid=(.*)')
    if rid is None:
        rid = match1(url, r'/(\d+)/?')
    if "album" in url:
        j = loads(get_content("http://music.163.com/api/album/%s?id=%s&csrf_token=" % (rid, rid), headers={"Referer": "http://music.163.com/"}))

        artist_name = j['album']['artists'][0]['name']
        album_name = j['album']['name'].strip()
        new_dir = output_dir + '/' + fs.legitimize("%s - %s" % (artist_name, album_name))
        if not info_only:
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
            cover_url = j['album']['picUrl']
            download_urls([cover_url], "cover", "jpg", 0, new_dir)

        for i in j['album']['songs']:
            netease_song_download(i, output_dir=new_dir, info_only=info_only)
            try: # download lyrics
                assert kwargs['caption']
                l = loads(get_content("http://music.163.com/api/song/lyric/?id=%s&lv=-1&csrf_token=" % i['id'], headers={"Referer": "http://music.163.com/"}))
                netease_lyric_download(i, l["lrc"]["lyric"], output_dir=new_dir, info_only=info_only)
            except: pass

    elif "playlist" in url:
        j = loads(get_content("http://music.163.com/api/playlist/detail?id=%s&csrf_token=" % rid, headers={"Referer": "http://music.163.com/"}))

        new_dir = output_dir + '/' + fs.legitimize(j['result']['name'])
        if not info_only:
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
            cover_url = j['result']['coverImgUrl']
            download_urls([cover_url], "cover", "jpg", 0, new_dir)

        prefix_width = len(str(len(j['result']['tracks'])))
        for n, i in enumerate(j['result']['tracks']):
            playlist_prefix = '%%.%dd_' % prefix_width % n
            netease_song_download(i, output_dir=new_dir, info_only=info_only, playlist_prefix=playlist_prefix)
            try: # download lyrics
                assert kwargs['caption']
                l = loads(get_content("http://music.163.com/api/song/lyric/?id=%s&lv=-1&csrf_token=" % i['id'], headers={"Referer": "http://music.163.com/"}))
                netease_lyric_download(i, l["lrc"]["lyric"], output_dir=new_dir, info_only=info_only, playlist_prefix=playlist_prefix)
            except: pass

    elif "song" in url:
        j = loads(get_content("http://music.163.com/api/song/detail/?id=%s&ids=[%s]&csrf_token=" % (rid, rid), headers={"Referer": "http://music.163.com/"}))
        netease_song_download(j["songs"][0], output_dir=output_dir, info_only=info_only)
        try: # download lyrics
            assert kwargs['caption']
            l = loads(get_content("http://music.163.com/api/song/lyric/?id=%s&lv=-1&csrf_token=" % rid, headers={"Referer": "http://music.163.com/"}))
            netease_lyric_download(j["songs"][0], l["lrc"]["lyric"], output_dir=output_dir, info_only=info_only)
        except: pass

    elif "program" in url:
        j = loads(get_content("http://music.163.com/api/dj/program/detail/?id=%s&ids=[%s]&csrf_token=" % (rid, rid), headers={"Referer": "http://music.163.com/"}))
        netease_song_download(j["program"]["mainSong"], output_dir=output_dir, info_only=info_only)

    elif "radio" in url:
        offset = 0
        while True:
            j = loads(get_content("http://music.163.com/api/dj/program/byradio/?radioId=%s&ids=[%s]&csrf_token=&offset=%d" % (rid, rid, offset), headers={"Referer": "http://music.163.com/"}))
            for i in j['programs']:
                netease_song_download(i["mainSong"], output_dir=output_dir, info_only=info_only)
            if not j['more']:
                break
            offset += len(j['programs'])

    elif "mv" in url:
        j = loads(get_content("http://music.163.com/api/mv/detail/?id=%s&ids=[%s]&csrf_token=" % (rid, rid), headers={"Referer": "http://music.163.com/"}))
        netease_video_download(j['data'], output_dir=output_dir, info_only=info_only)