def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        if '>Programmet er ikke længere tilgængeligt' in webpage:
            raise ExtractorError(
                'Video %s is not available' % video_id, expected=True)

        video_id = self._search_regex(
            (r'data-(?:material-identifier|episode-slug)="([^"]+)"',
             r'data-resource="[^>"]+mu/programcard/expanded/([^"]+)"'),
            webpage, 'video id', default=None)

        if not video_id:
            video_id = self._search_regex(
                r'(urn(?:%3A|:)dr(?:%3A|:)mu(?:%3A|:)programcard(?:%3A|:)[\da-f]+)',
                webpage, 'urn', default=None)
            if video_id:
                video_id = compat_urllib_parse_unquote(video_id)

        _PROGRAMCARD_BASE = 'https://www.dr.dk/mu-online/api/1.4/programcard'
        query = {'expanded': 'true'}

        if video_id:
            programcard_url = '%s/%s' % (_PROGRAMCARD_BASE, video_id)
        else:
            programcard_url = _PROGRAMCARD_BASE
            page = self._parse_json(
                self._search_regex(
                    r'data\s*=\s*({.+?})\s*(?:;|</script)', webpage,
                    'data'), '1')['cache']['page']
            page = page[list(page.keys())[0]]
            item = try_get(
                page, (lambda x: x['item'], lambda x: x['entries'][0]['item']),
                dict)
            video_id = item['customId'].split(':')[-1]
            query['productionnumber'] = video_id

        data = self._download_json(
            programcard_url, video_id, 'Downloading video JSON', query=query)

        title = str_or_none(data.get('Title')) or re.sub(
            r'\s*\|\s*(?:TV\s*\|\s*DR|DRTV)$', '',
            self._og_search_title(webpage))
        description = self._og_search_description(
            webpage, default=None) or data.get('Description')

        timestamp = unified_timestamp(
            data.get('PrimaryBroadcastStartTime') or data.get('SortDateTime'))

        thumbnail = None
        duration = None

        restricted_to_denmark = False

        formats = []
        subtitles = {}

        assets = []
        primary_asset = data.get('PrimaryAsset')
        if isinstance(primary_asset, dict):
            assets.append(primary_asset)
        secondary_assets = data.get('SecondaryAssets')
        if isinstance(secondary_assets, list):
            for secondary_asset in secondary_assets:
                if isinstance(secondary_asset, dict):
                    assets.append(secondary_asset)

        def hex_to_bytes(hex):
            return binascii.a2b_hex(hex.encode('ascii'))

        def decrypt_uri(e):
            n = int(e[2:10], 16)
            a = e[10 + n:]
            data = bytes_to_intlist(hex_to_bytes(e[10:10 + n]))
            key = bytes_to_intlist(hashlib.sha256(
                ('%s:sRBzYNXBzkKgnjj8pGtkACch' % a).encode('utf-8')).digest())
            iv = bytes_to_intlist(hex_to_bytes(a))
            decrypted = aes_cbc_decrypt(data, key, iv)
            return intlist_to_bytes(
                decrypted[:-decrypted[-1]]).decode('utf-8').split('?')[0]

        for asset in assets:
            kind = asset.get('Kind')
            if kind == 'Image':
                thumbnail = url_or_none(asset.get('Uri'))
            elif kind in ('VideoResource', 'AudioResource'):
                duration = float_or_none(asset.get('DurationInMilliseconds'), 1000)
                restricted_to_denmark = asset.get('RestrictedToDenmark')
                asset_target = asset.get('Target')
                for link in asset.get('Links', []):
                    uri = link.get('Uri')
                    if not uri:
                        encrypted_uri = link.get('EncryptedUri')
                        if not encrypted_uri:
                            continue
                        try:
                            uri = decrypt_uri(encrypted_uri)
                        except Exception:
                            self.report_warning(
                                'Unable to decrypt EncryptedUri', video_id)
                            continue
                    uri = url_or_none(uri)
                    if not uri:
                        continue
                    target = link.get('Target')
                    format_id = target or ''
                    if asset_target in ('SpokenSubtitles', 'SignLanguage', 'VisuallyInterpreted'):
                        preference = -1
                        format_id += '-%s' % asset_target
                    elif asset_target == 'Default':
                        preference = 1
                    else:
                        preference = None
                    if target == 'HDS':
                        f4m_formats = self._extract_f4m_formats(
                            uri + '?hdcore=3.3.0&plugin=aasp-3.3.0.99.43',
                            video_id, preference, f4m_id=format_id, fatal=False)
                        if kind == 'AudioResource':
                            for f in f4m_formats:
                                f['vcodec'] = 'none'
                        formats.extend(f4m_formats)
                    elif target == 'HLS':
                        formats.extend(self._extract_m3u8_formats(
                            uri, video_id, 'mp4', entry_protocol='m3u8_native',
                            preference=preference, m3u8_id=format_id,
                            fatal=False))
                    else:
                        bitrate = link.get('Bitrate')
                        if bitrate:
                            format_id += '-%s' % bitrate
                        formats.append({
                            'url': uri,
                            'format_id': format_id,
                            'tbr': int_or_none(bitrate),
                            'ext': link.get('FileFormat'),
                            'vcodec': 'none' if kind == 'AudioResource' else None,
                            'preference': preference,
                        })
            subtitles_list = asset.get('SubtitlesList') or asset.get('Subtitleslist')
            if isinstance(subtitles_list, list):
                LANGS = {
                    'Danish': 'da',
                }
                for subs in subtitles_list:
                    if not isinstance(subs, dict):
                        continue
                    sub_uri = url_or_none(subs.get('Uri'))
                    if not sub_uri:
                        continue
                    lang = subs.get('Language') or 'da'
                    subtitles.setdefault(LANGS.get(lang, lang), []).append({
                        'url': sub_uri,
                        'ext': mimetype2ext(subs.get('MimeType')) or 'vtt'
                    })

        if not formats and restricted_to_denmark:
            self.raise_geo_restricted(
                'Unfortunately, DR is not allowed to show this program outside Denmark.',
                countries=self._GEO_COUNTRIES)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
            'series': str_or_none(data.get('SeriesTitle')),
            'season': str_or_none(data.get('SeasonTitle')),
            'season_number': int_or_none(data.get('SeasonNumber')),
            'season_id': str_or_none(data.get('SeasonUrn')),
            'episode': str_or_none(data.get('EpisodeTitle')),
            'episode_number': int_or_none(data.get('EpisodeNumber')),
            'release_year': int_or_none(data.get('ProductionYear')),
        }