def _parse_config(self, config, video_id):
        video_data = config['video']
        video_title = video_data['title']
        live_event = video_data.get('live_event') or {}
        is_live = live_event.get('status') == 'started'
        request = config.get('request') or {}

        formats = []
        config_files = video_data.get('files') or request.get('files') or {}
        for f in (config_files.get('progressive') or []):
            video_url = f.get('url')
            if not video_url:
                continue
            formats.append({
                'url': video_url,
                'format_id': 'http-%s' % f.get('quality'),
                'width': int_or_none(f.get('width')),
                'height': int_or_none(f.get('height')),
                'fps': int_or_none(f.get('fps')),
                'tbr': int_or_none(f.get('bitrate')),
            })

        # TODO: fix handling of 308 status code returned for live archive manifest requests
        sep_pattern = r'/sep/video/'
        for files_type in ('hls', 'dash'):
            for cdn_name, cdn_data in (try_get(config_files, lambda x: x[files_type]['cdns']) or {}).items():
                manifest_url = cdn_data.get('url')
                if not manifest_url:
                    continue
                format_id = '%s-%s' % (files_type, cdn_name)
                sep_manifest_urls = []
                if re.search(sep_pattern, manifest_url):
                    for suffix, repl in (('', 'video'), ('_sep', 'sep/video')):
                        sep_manifest_urls.append((format_id + suffix, re.sub(
                            sep_pattern, '/%s/' % repl, manifest_url)))
                else:
                    sep_manifest_urls = [(format_id, manifest_url)]
                for f_id, m_url in sep_manifest_urls:
                    if files_type == 'hls':
                        formats.extend(self._extract_m3u8_formats(
                            m_url, video_id, 'mp4',
                            'm3u8' if is_live else 'm3u8_native', m3u8_id=f_id,
                            note='Downloading %s m3u8 information' % cdn_name,
                            fatal=False))
                    elif files_type == 'dash':
                        if 'json=1' in m_url:
                            real_m_url = (self._download_json(m_url, video_id, fatal=False) or {}).get('url')
                            if real_m_url:
                                m_url = real_m_url
                        mpd_formats = self._extract_mpd_formats(
                            m_url.replace('/master.json', '/master.mpd'), video_id, f_id,
                            'Downloading %s MPD information' % cdn_name,
                            fatal=False)
                        formats.extend(mpd_formats)

        live_archive = live_event.get('archive') or {}
        live_archive_source_url = live_archive.get('source_url')
        if live_archive_source_url and live_archive.get('status') == 'done':
            formats.append({
                'format_id': 'live-archive-source',
                'url': live_archive_source_url,
                'preference': 1,
            })

        for f in formats:
            if f.get('vcodec') == 'none':
                f['preference'] = -50
            elif f.get('acodec') == 'none':
                f['preference'] = -40

        subtitles = {}
        for tt in (request.get('text_tracks') or []):
            subtitles[tt['lang']] = [{
                'ext': 'vtt',
                'url': urljoin('https://vimeo.com', tt['url']),
            }]

        thumbnails = []
        if not is_live:
            for key, thumb in (video_data.get('thumbs') or {}).items():
                thumbnails.append({
                    'id': key,
                    'width': int_or_none(key),
                    'url': thumb,
                })
            thumbnail = video_data.get('thumbnail')
            if thumbnail:
                thumbnails.append({
                    'url': thumbnail,
                })

        owner = video_data.get('owner') or {}
        video_uploader_url = owner.get('url')

        return {
            'id': str_or_none(video_data.get('id')) or video_id,
            'title': self._live_title(video_title) if is_live else video_title,
            'uploader': owner.get('name'),
            'uploader_id': video_uploader_url.split('/')[-1] if video_uploader_url else None,
            'uploader_url': video_uploader_url,
            'thumbnails': thumbnails,
            'duration': int_or_none(video_data.get('duration')),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
        }