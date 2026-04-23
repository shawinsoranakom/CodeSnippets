def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(f'https://www.cbc.ca/player/play/{video_id}', video_id)
        data = self._search_json(
            r'window\.__INITIAL_STATE__\s*=', webpage,
            'initial state', video_id, transform_source=js_to_json)['video']['currentClip']
        assets = traverse_obj(
            data, ('media', 'assets', lambda _, v: url_or_none(v['key']) and v['type']))

        if not assets and (media_id := traverse_obj(data, ('mediaId', {str}))):
            # XXX: Deprecated; CBC is migrating off of ThePlatform
            return {
                '_type': 'url_transparent',
                'ie_key': 'ThePlatform',
                'url': smuggle_url(
                    f'http://link.theplatform.com/s/ExhSPC/media/guid/2655402169/{media_id}?mbr=true&formats=MPEG4,FLV,MP3', {
                        'force_smil_url': True,
                    }),
                'id': media_id,
                '_format_sort_fields': ('res', 'proto'),  # Prioritize direct http formats over HLS
            }

        is_live = traverse_obj(data, ('media', 'streamType', {str})) == 'Live'
        formats, subtitles = [], {}

        for sub in traverse_obj(data, ('media', 'textTracks', lambda _, v: url_or_none(v['src']))):
            subtitles.setdefault(sub.get('language') or 'und', []).append({
                'url': sub['src'],
                'name': sub.get('label'),
            })

        for asset in assets:
            asset_key = asset['key']
            asset_type = asset['type']
            if asset_type != 'medianet':
                self.report_warning(f'Skipping unsupported asset type "{asset_type}": {asset_key}')
                continue
            asset_data = self._download_json(asset_key, video_id, f'Downloading {asset_type} JSON')
            ext = mimetype2ext(self._parse_param(asset_data, 'contentType'))
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    asset_data['url'], video_id, 'mp4', m3u8_id='hls', live=is_live)
                formats.extend(fmts)
                # Avoid slow/error-prone webvtt-over-m3u8 if direct https vtt is available
                if not subtitles:
                    self._merge_subtitles(subs, target=subtitles)
                if is_live or not fmts:
                    continue
                # Check for direct https mp4 format
                best_video_fmt = traverse_obj(fmts, (
                    lambda _, v: v.get('vcodec') != 'none' and v['tbr'], all,
                    {functools.partial(sorted, key=lambda x: x['tbr'])}, -1, {dict})) or {}
                base_url = self._search_regex(
                    r'(https?://[^?#]+?/)hdntl=', best_video_fmt.get('url'), 'base url', default=None)
                if not base_url or '/live/' in base_url:
                    continue
                mp4_url = base_url + replace_extension(url_basename(best_video_fmt['url']), 'mp4')
                if self._request_webpage(
                        HEADRequest(mp4_url), video_id, 'Checking for https format',
                        errnote=False, fatal=False):
                    formats.append({
                        **best_video_fmt,
                        'url': mp4_url,
                        'format_id': 'https-mp4',
                        'protocol': 'https',
                        'manifest_url': None,
                        'acodec': None,
                    })
            else:
                formats.append({
                    'url': asset_data['url'],
                    'ext': ext,
                    'vcodec': 'none' if self._parse_param(asset_data, 'mediaType') == 'audio' else None,
                })

        chapters = traverse_obj(data, (
            'media', 'chapters', lambda _, v: float(v['startTime']) is not None, {
                'start_time': ('startTime', {float_or_none(scale=1000)}),
                'end_time': ('endTime', {float_or_none(scale=1000)}),
                'title': ('name', {str}),
            }))
        # Filter out pointless single chapters with start_time==0 and no end_time
        if len(chapters) == 1 and not (chapters[0].get('start_time') or chapters[0].get('end_time')):
            chapters = []

        return {
            **traverse_obj(data, {
                'title': ('title', {str}),
                'description': ('description', {str.strip}),
                'thumbnail': ('image', 'url', {url_or_none}, {update_url(query=None)}),
                'timestamp': ('publishedAt', {float_or_none(scale=1000)}),
                'media_type': ('media', 'clipType', {str}),
                'series': ('showName', {str}),
                'season_number': ('media', 'season', {int_or_none}),
                'duration': ('media', 'duration', {float_or_none}, {lambda x: None if is_live else x}),
                'location': ('media', 'region', {str}),
                'tags': ('tags', ..., 'name', {str}),
                'genres': ('media', 'genre', all),
                'categories': ('categories', ..., 'name', {str}),
            }),
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'chapters': chapters,
            'is_live': is_live,
        }