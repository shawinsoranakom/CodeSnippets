def _extract_formats(self, video_id, station, is_onair, ft, cursor, auth_token, area_id, query):
        m3u8_playlist_data = self._download_xml(
            f'https://radiko.jp/v3/station/stream/pc_html5/{station}.xml', video_id,
            note='Downloading stream information')

        formats = []
        found = set()

        timefree_int = 0 if is_onair else 1

        for element in m3u8_playlist_data.findall(f'.//url[@timefree="{timefree_int}"]/playlist_create_url'):
            pcu = element.text
            if pcu in found:
                continue
            found.add(pcu)
            playlist_url = update_url_query(pcu, {
                'station_id': station,
                **query,
                'l': '15',
                'lsid': ''.join(random.choices('0123456789abcdef', k=32)),
                'type': 'b',
            })

            time_to_skip = None if is_onair else cursor - ft

            domain = urllib.parse.urlparse(playlist_url).netloc
            subformats = self._extract_m3u8_formats(
                playlist_url, video_id, ext='m4a',
                live=True, fatal=False, m3u8_id=domain,
                note=f'Downloading m3u8 information from {domain}',
                headers={
                    'X-Radiko-AreaId': area_id,
                    'X-Radiko-AuthToken': auth_token,
                })
            for sf in subformats:
                if (is_onair ^ pcu.startswith(self._HOSTS_FOR_LIVE)) or (
                        not is_onair and pcu.startswith(self._HOSTS_FOR_TIME_FREE_FFMPEG_UNSUPPORTED)):
                    sf['preference'] = -100
                    sf['format_note'] = 'not preferred'
                if not is_onair and timefree_int == 1 and time_to_skip:
                    sf['downloader_options'] = {'ffmpeg_args': ['-ss', str(time_to_skip)]}
            formats.extend(subformats)

        return formats