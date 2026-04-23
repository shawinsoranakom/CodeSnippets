def extract_format(page, version):
            json_str = self._html_search_regex(
                r'player_data=(\\?["\'])(?P<player_data>.+?)\1', page,
                f'{version} player_json', fatal=False, group='player_data')
            if not json_str:
                return
            player_data = self._parse_json(
                json_str, f'{version} player_data', fatal=False)
            if not player_data:
                return
            video = player_data.get('video')
            if not video or 'file' not in video:
                self.report_warning(f'Unable to extract {version} version information')
                return
            video_quality = video.get('quality')
            qualities = video.get('qualities', {})
            video_quality = next((k for k, v in qualities.items() if v == video_quality), video_quality)
            if video.get('file'):
                if video['file'].startswith('uggc'):
                    video['file'] = codecs.decode(video['file'], 'rot_13')
                    if video['file'].endswith('adc.mp4'):
                        video['file'] = video['file'].replace('adc.mp4', '.mp4')
                elif not video['file'].startswith('http'):
                    video['file'] = decrypt_file(video['file'])
                info_dict['formats'].append({
                    'url': video['file'],
                    'format_id': video_quality,
                    'height': int_or_none(video_quality[:-1]),
                })
            for quality, cda_quality in qualities.items():
                if quality == video_quality:
                    continue
                data = {'jsonrpc': '2.0', 'method': 'videoGetLink', 'id': 2,
                        'params': [video_id, cda_quality, video.get('ts'), video.get('hash2'), {}]}
                data = json.dumps(data).encode()
                response = self._download_json(
                    f'https://www.cda.pl/video/{video_id}', video_id, headers={
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                    }, data=data, note=f'Fetching {quality} url',
                    errnote=f'Failed to fetch {quality} url', fatal=False)
                if (
                    traverse_obj(response, ('result', 'status')) != 'ok'
                    or not traverse_obj(response, ('result', 'resp', {url_or_none}))
                ):
                    continue
                video_url = response['result']['resp']
                ext = determine_ext(video_url)
                if ext == 'mpd':
                    info_dict['formats'].extend(self._extract_mpd_formats(
                        video_url, video_id, mpd_id='dash', fatal=False))
                elif ext == 'm3u8':
                    info_dict['formats'].extend(self._extract_m3u8_formats(
                        video_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
                else:
                    info_dict['formats'].append({
                        'url': video_url,
                        'format_id': quality,
                        'height': int_or_none(quality[:-1]),
                    })

            if not info_dict['duration']:
                info_dict['duration'] = parse_duration(video.get('duration'))