def process_video_files(v):
            nonlocal video_id
            for video_file in v:
                v_url = video_file.get('url')
                if not v_url:
                    continue
                if video_file.get('type') == 'application/deferred':
                    d_param = urllib.parse.quote(v_url)
                    token = video_file.get('token')
                    if not token:
                        continue
                    deferred_json = self._download_json(
                        f'https://api.tv5monde.com/player/asset/{d_param}/resolve?condenseKS=true',
                        display_id, 'Downloading deferred info', fatal=False, impersonate=True,
                        headers={'Authorization': f'Bearer {token}'})
                    v_url = traverse_obj(deferred_json, (0, 'url', {url_or_none}))
                    if not v_url:
                        continue
                    # data-guid from the webpage isn't stable, use the material id from the json urls
                    video_id = self._search_regex(
                        r'materials/([\da-zA-Z]{10}_[\da-fA-F]{7})/', v_url, 'video id', default=None)
                    process_video_files(deferred_json)

                video_format = video_file.get('format') or determine_ext(v_url)
                if video_format == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        v_url, display_id, 'mp4', 'm3u8_native',
                        m3u8_id='hls', fatal=False))
                elif video_format == 'mpd':
                    formats.extend(self._extract_mpd_formats(
                        v_url, display_id, fatal=False))
                else:
                    formats.append({
                        'url': v_url,
                        'format_id': video_format,
                    })