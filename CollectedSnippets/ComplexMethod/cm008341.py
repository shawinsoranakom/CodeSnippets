def _web_extract(self, video_id):
        self._set_cookie('cda.pl', 'cda.player', 'html5')
        webpage, urlh = self._download_webpage_handle(
            f'{self._BASE_URL}/video/{video_id}/vfilm', video_id)

        if 'Ten film jest dostępny dla użytkowników premium' in webpage:
            self.raise_login_required('This video is only available for premium users')

        if re.search(r'niedostępn[ey] w(?:&nbsp;|\s+)Twoim kraju\s*<', webpage):
            self.raise_geo_restricted()

        need_confirm_age = False
        if self._html_search_regex(r'(<button[^>]+name="[^"]*age_confirm[^"]*")',
                                   webpage, 'birthday validate form', default=None):
            webpage = self._download_age_confirm_page(
                urlh.url, video_id, note='Confirming age')
            need_confirm_age = True

        formats = []

        uploader = self._search_regex(r'''(?x)
            <(span|meta)[^>]+itemprop=(["\'])author\2[^>]*>
            (?:<\1[^>]*>[^<]*</\1>|(?!</\1>)(?:.|\n))*?
            <(span|meta)[^>]+itemprop=(["\'])name\4[^>]*>(?P<uploader>[^<]+)</\3>
        ''', webpage, 'uploader', default=None, group='uploader')
        average_rating = self._search_regex(
            (r'<(?:span|meta)[^>]+itemprop=(["\'])ratingValue\1[^>]*>(?P<rating_value>[0-9.]+)',
             r'<span[^>]+\bclass=["\']rating["\'][^>]*>(?P<rating_value>[0-9.]+)'), webpage, 'rating', fatal=False,
            group='rating_value')

        info_dict = {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'uploader': uploader,
            'average_rating': float_or_none(average_rating),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
            'duration': None,
            'age_limit': 18 if need_confirm_age else 0,
        }

        info = self._search_json_ld(webpage, video_id, default={})

        # Source: https://www.cda.pl/js/player.js?t=1606154898
        def decrypt_file(a):
            for p in ('_XDDD', '_CDA', '_ADC', '_CXD', '_QWE', '_Q5', '_IKSDE'):
                a = a.replace(p, '')
            a = urllib.parse.unquote(a)
            b = []
            for c in a:
                f = compat_ord(c)
                b.append(chr(33 + (f + 14) % 94) if 33 <= f <= 126 else chr(f))
            a = ''.join(b)
            a = a.replace('.cda.mp4', '')
            for p in ('.2cda.pl', '.3cda.pl'):
                a = a.replace(p, '.cda.pl')
            if '/upstream' in a:
                a = a.replace('/upstream', '.mp4/upstream')
                return 'https://' + a
            return 'https://' + a + '.mp4'

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

        extract_format(webpage, 'default')

        for href, resolution in re.findall(
                r'<a[^>]+data-quality="[^"]+"[^>]+href="([^"]+)"[^>]+class="quality-btn"[^>]*>([0-9]+p)',
                webpage):
            if need_confirm_age:
                handler = self._download_age_confirm_page
            else:
                handler = self._download_webpage

            webpage = handler(
                urljoin(self._BASE_URL, href), video_id,
                f'Downloading {resolution} version information', fatal=False)
            if not webpage:
                # Manually report warning because empty page is returned when
                # invalid version is requested.
                self.report_warning(f'Unable to download {resolution} version information')
                continue

            extract_format(webpage, resolution)

        return merge_dicts(info_dict, info)