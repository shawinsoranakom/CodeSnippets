def extract_formats(node):
            for child in node:
                if child.tag.endswith('Files'):
                    extract_formats(child)
                elif child.tag.endswith('File'):
                    video_url = child.text
                    if (not video_url or video_url in processed_urls
                            or any(p in video_url for p in ('NOT_USED', 'NOT-USED'))):
                        continue
                    processed_urls.append(video_url)
                    ext = determine_ext(video_url)
                    auth_video_url = url_or_none(self._download_webpage(
                        f'{self._API_BASE}/auth/access/v2', video_id,
                        note=f'Downloading authenticated {ext} stream URL',
                        fatal=False, query={'stream': video_url}))
                    if auth_video_url:
                        processed_urls.append(auth_video_url)
                        video_url = auth_video_url
                    if ext == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            video_url, video_id, 'mp4',
                            entry_protocol='m3u8_native', m3u8_id='hls',
                            fatal=False))
                    elif ext == 'f4m':
                        formats.extend(self._extract_f4m_formats(
                            video_url, video_id, f4m_id='hds', fatal=False))
                    elif ext == 'mpd':
                        # video-only and audio-only streams are of different
                        # duration resulting in out of sync issue
                        continue
                        formats.extend(self._extract_mpd_formats(
                            video_url, video_id, mpd_id='dash', fatal=False))
                    elif ext == 'mp3' or child.tag == 'AudioMediaFile':
                        formats.append({
                            'format_id': 'audio',
                            'url': video_url,
                            'vcodec': 'none',
                        })
                    else:
                        proto = urllib.parse.urlparse(video_url).scheme
                        if not child.tag.startswith('HTTP') and proto != 'rtmp':
                            continue
                        preference = -1 if proto == 'rtmp' else 1
                        label = child.get('label')
                        tbr = int_or_none(child.get('bitrate'))
                        format_id = f'{proto}-{label if label else tbr}' if label or tbr else proto
                        if not self._is_valid_url(video_url, video_id, format_id):
                            continue
                        width, height = (int_or_none(x) for x in child.get('resolution', 'x').split('x')[:2])
                        formats.append({
                            'format_id': format_id,
                            'url': video_url,
                            'width': width,
                            'height': height,
                            'tbr': tbr,
                            'preference': preference,
                        })