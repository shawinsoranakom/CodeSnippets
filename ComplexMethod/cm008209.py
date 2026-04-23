def _parse_config(self, config, video_id):
        video_data = config['video']
        video_title = video_data.get('title')
        live_event = video_data.get('live_event') or {}
        live_status = {
            'pending': 'is_upcoming',
            'active': 'is_upcoming',
            'started': 'is_live',
            'ended': 'post_live',
        }.get(live_event.get('status'))
        is_live = live_status == 'is_live'
        request = config.get('request') or {}

        formats = []
        subtitles = {}

        config_files = video_data.get('files') or request.get('files') or {}
        for f in (config_files.get('progressive') or []):
            video_url = f.get('url')
            if not video_url:
                continue
            formats.append({
                'url': video_url,
                'format_id': 'http-{}'.format(f.get('quality')),
                'source_preference': 10,
                'width': int_or_none(f.get('width')),
                'height': int_or_none(f.get('height')),
                'fps': int_or_none(f.get('fps')),
                'tbr': int_or_none(f.get('bitrate')),
            })

        # TODO: fix handling of 308 status code returned for live archive manifest requests
        QUALITIES = ('low', 'medium', 'high')
        quality = qualities(QUALITIES)
        sep_pattern = r'/sep/video/'
        for files_type in ('hls', 'dash'):
            for cdn_name, cdn_data in (try_get(config_files, lambda x: x[files_type]['cdns']) or {}).items():
                # TODO: Also extract 'avc_url'? Investigate if there are 'hevc_url', 'av1_url'?
                manifest_url = cdn_data.get('url')
                if not manifest_url:
                    continue
                format_id = f'{files_type}-{cdn_name}'
                sep_manifest_urls = []
                if re.search(sep_pattern, manifest_url):
                    for suffix, repl in (('', 'video'), ('_sep', 'sep/video')):
                        sep_manifest_urls.append((format_id + suffix, re.sub(
                            sep_pattern, f'/{repl}/', manifest_url)))
                else:
                    sep_manifest_urls = [(format_id, manifest_url)]
                for f_id, m_url in sep_manifest_urls:
                    if files_type == 'hls':
                        fmts, subs = self._extract_m3u8_formats_and_subtitles(
                            m_url, video_id, 'mp4', live=is_live, m3u8_id=f_id,
                            note=f'Downloading {cdn_name} m3u8 information',
                            fatal=False)
                        # m3u8 doesn't give audio bitrates; need to prioritize based on GROUP-ID
                        # See: https://github.com/yt-dlp/yt-dlp/issues/10854
                        for f in fmts:
                            if mobj := re.search(rf'audio-({"|".join(QUALITIES)})', f['format_id']):
                                f['quality'] = quality(mobj.group(1))
                        formats.extend(fmts)
                        self._merge_subtitles(subs, target=subtitles)
                    elif files_type == 'dash':
                        if 'json=1' in m_url:
                            real_m_url = (self._download_json(m_url, video_id, fatal=False) or {}).get('url')
                            if real_m_url:
                                m_url = real_m_url
                        fmts, subs = self._extract_mpd_formats_and_subtitles(
                            m_url.replace('/master.json', '/master.mpd'), video_id, f_id,
                            f'Downloading {cdn_name} MPD information',
                            fatal=False)
                        formats.extend(fmts)
                        self._merge_subtitles(subs, target=subtitles)

        live_archive = live_event.get('archive') or {}
        live_archive_source_url = live_archive.get('source_url')
        if live_archive_source_url and live_archive.get('status') == 'done':
            formats.append({
                'format_id': 'live-archive-source',
                'url': live_archive_source_url,
                'quality': 10,
            })

        for tt in (request.get('text_tracks') or []):
            subtitles.setdefault(tt['lang'], []).append({
                'ext': 'vtt',
                'url': urljoin('https://player.vimeo.com/', tt['url']),
            })

        thumbnails = []
        if not is_live:
            for key, thumb in (video_data.get('thumbs') or {}).items():
                thumbnails.append({
                    'id': key,
                    'width': int_or_none(key),
                    'url': thumb,
                })
            thumbnails.extend(traverse_obj(video_data, (('thumbnail', 'thumbnail_url'), {'url': {url_or_none}})))

        owner = video_data.get('owner') or {}
        video_uploader_url = owner.get('url')

        return {
            'id': str_or_none(video_data.get('id')) or video_id,
            'title': video_title,
            'uploader': owner.get('name'),
            'uploader_id': video_uploader_url.split('/')[-1] if video_uploader_url else None,
            'uploader_url': video_uploader_url,
            'thumbnails': thumbnails,
            'duration': int_or_none(video_data.get('duration')),
            'chapters': sorted(traverse_obj(config, (
                'embed', 'chapters', lambda _, v: int(v['timecode']) is not None, {
                    'title': ('title', {str}),
                    'start_time': ('timecode', {int_or_none}),
                })), key=lambda c: c['start_time']) or None,
            'formats': formats,
            'subtitles': subtitles,
            'live_status': live_status,
            'release_timestamp': traverse_obj(live_event, ('ingest', (
                ('scheduled_start_time', {parse_iso8601}),
                ('start_time', {int_or_none}),
            ), any)),
            # Note: Bitrates are completely broken. Single m3u8 may contain entries in kbps and bps
            # at the same time without actual units specified.
            '_format_sort_fields': ('quality', 'res', 'fps', 'hdr:12', 'source'),
        }