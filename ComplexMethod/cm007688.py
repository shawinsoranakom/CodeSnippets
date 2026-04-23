def extract_info(html, video_id, num=None):
            title, description = [None] * 2
            formats = []

            for input_ in re.findall(
                    r'<input[^>]+class=["\'].*?streamstarter[^>]+>', html):
                attributes = extract_attributes(input_)
                title = attributes.get('data-dialog-header')
                playlist_urls = []
                for playlist_key in ('data-playlist', 'data-otherplaylist', 'data-stream'):
                    playlist_url = attributes.get(playlist_key)
                    if isinstance(playlist_url, compat_str) and re.match(
                            r'/?[\da-zA-Z]+', playlist_url):
                        playlist_urls.append(attributes[playlist_key])
                if not playlist_urls:
                    continue

                lang = attributes.get('data-lang')
                lang_note = attributes.get('value')

                for playlist_url in playlist_urls:
                    kind = self._search_regex(
                        r'videomaterialurl/\d+/([^/]+)/',
                        playlist_url, 'media kind', default=None)
                    format_id_list = []
                    if lang:
                        format_id_list.append(lang)
                    if kind:
                        format_id_list.append(kind)
                    if not format_id_list and num is not None:
                        format_id_list.append(compat_str(num))
                    format_id = '-'.join(format_id_list)
                    format_note = ', '.join(filter(None, (kind, lang_note)))
                    item_id_list = []
                    if format_id:
                        item_id_list.append(format_id)
                    item_id_list.append('videomaterial')
                    playlist = self._download_json(
                        urljoin(url, playlist_url), video_id,
                        'Downloading %s JSON' % ' '.join(item_id_list),
                        headers={
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRF-Token': csrf_token,
                            'Referer': url,
                            'Accept': 'application/json, text/javascript, */*; q=0.01',
                        }, fatal=False)
                    if not playlist:
                        continue
                    stream_url = url_or_none(playlist.get('streamurl'))
                    if stream_url:
                        rtmp = re.search(
                            r'^(?P<url>rtmpe?://(?P<host>[^/]+)/(?P<app>.+/))(?P<playpath>mp[34]:.+)',
                            stream_url)
                        if rtmp:
                            formats.append({
                                'url': rtmp.group('url'),
                                'app': rtmp.group('app'),
                                'play_path': rtmp.group('playpath'),
                                'page_url': url,
                                'player_url': 'https://www.anime-on-demand.de/assets/jwplayer.flash-55abfb34080700304d49125ce9ffb4a6.swf',
                                'rtmp_real_time': True,
                                'format_id': 'rtmp',
                                'ext': 'flv',
                            })
                            continue
                    start_video = playlist.get('startvideo', 0)
                    playlist = playlist.get('playlist')
                    if not playlist or not isinstance(playlist, list):
                        continue
                    playlist = playlist[start_video]
                    title = playlist.get('title')
                    if not title:
                        continue
                    description = playlist.get('description')
                    for source in playlist.get('sources', []):
                        file_ = source.get('file')
                        if not file_:
                            continue
                        ext = determine_ext(file_)
                        format_id_list = [lang, kind]
                        if ext == 'm3u8':
                            format_id_list.append('hls')
                        elif source.get('type') == 'video/dash' or ext == 'mpd':
                            format_id_list.append('dash')
                        format_id = '-'.join(filter(None, format_id_list))
                        if ext == 'm3u8':
                            file_formats = self._extract_m3u8_formats(
                                file_, video_id, 'mp4',
                                entry_protocol='m3u8_native', m3u8_id=format_id, fatal=False)
                        elif source.get('type') == 'video/dash' or ext == 'mpd':
                            continue
                            file_formats = self._extract_mpd_formats(
                                file_, video_id, mpd_id=format_id, fatal=False)
                        else:
                            continue
                        for f in file_formats:
                            f.update({
                                'language': lang,
                                'format_note': format_note,
                            })
                        formats.extend(file_formats)

            return {
                'title': title,
                'description': description,
                'formats': formats,
            }