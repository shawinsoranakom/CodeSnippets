def _real_extract(self, url):
        video_id = self._match_id(url)

        data = json.dumps({
            'method': 'da.content.get',
            'params': [
                video_id, {
                    'site': 's%d',
                    'referrer': f'http://www.ivi.ru/watch/{video_id}',
                    'contentid': video_id,
                },
            ],
        })

        for site in (353, 183):
            content_data = (data % site).encode()
            if site == 353:
                if not Cryptodome.CMAC:
                    continue

                timestamp = (self._download_json(
                    self._LIGHT_URL, video_id,
                    'Downloading timestamp JSON', data=json.dumps({
                        'method': 'da.timestamp.get',
                        'params': [],
                    }).encode(), fatal=False) or {}).get('result')
                if not timestamp:
                    continue

                query = {
                    'ts': timestamp,
                    'sign': Cryptodome.CMAC.new(self._LIGHT_KEY, timestamp.encode() + content_data,
                                                Cryptodome.Blowfish).hexdigest(),
                }
            else:
                query = {}

            video_json = self._download_json(
                self._LIGHT_URL, video_id,
                'Downloading video JSON', data=content_data, query=query)

            error = video_json.get('error')
            if error:
                origin = error.get('origin')
                message = error.get('message') or error.get('user_message')
                extractor_msg = 'Unable to download video %s'
                if origin == 'NotAllowedForLocation':
                    self.raise_geo_restricted(message, self._GEO_COUNTRIES)
                elif origin == 'NoRedisValidData':
                    extractor_msg = 'Video %s does not exist'
                elif site == 353:
                    continue
                elif not Cryptodome.CMAC:
                    raise ExtractorError('pycryptodomex not found. Please install', expected=True)
                elif message:
                    extractor_msg += ': ' + message
                raise ExtractorError(extractor_msg % video_id, expected=True)
            else:
                break

        result = video_json['result']
        title = result['title']

        quality = qualities(self._KNOWN_FORMATS)

        formats = []
        for f in result.get('files', []):
            f_url = f.get('url')
            content_format = f.get('content_format')
            if not f_url:
                continue
            if (not self.get_param('allow_unplayable_formats')
                    and ('-MDRM-' in content_format or '-FPS-' in content_format)):
                continue
            formats.append({
                'url': f_url,
                'format_id': content_format,
                'quality': quality(content_format),
                'filesize': int_or_none(f.get('size_in_bytes')),
            })

        compilation = result.get('compilation')
        episode = title if compilation else None

        title = f'{compilation} - {title}' if compilation is not None else title

        thumbnails = [{
            'url': preview['url'],
            'id': preview.get('content_format'),
        } for preview in result.get('preview', []) if preview.get('url')]

        webpage = self._download_webpage(url, video_id)

        season = self._search_regex(
            r'<li[^>]+class="season active"[^>]*><a[^>]+>([^<]+)',
            webpage, 'season', default=None)
        season_number = int_or_none(self._search_regex(
            r'<li[^>]+class="season active"[^>]*><a[^>]+data-season(?:-index)?="(\d+)"',
            webpage, 'season number', default=None))

        episode_number = int_or_none(self._search_regex(
            r'[^>]+itemprop="episode"[^>]*>\s*<meta[^>]+itemprop="episodeNumber"[^>]+content="(\d+)',
            webpage, 'episode number', default=None))

        description = self._og_search_description(webpage, default=None) or self._html_search_meta(
            'description', webpage, 'description', default=None)

        return {
            'id': video_id,
            'title': title,
            'series': compilation,
            'season': season,
            'season_number': season_number,
            'episode': episode,
            'episode_number': episode_number,
            'thumbnails': thumbnails,
            'description': description,
            'duration': int_or_none(result.get('duration')),
            'formats': formats,
        }