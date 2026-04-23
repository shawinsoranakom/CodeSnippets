def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id') or mobj.group('id_s')

        ppjson = self._download_json(
            'http://www.ndr.de/%s-ppjson.json' % video_id, video_id)

        playlist = ppjson['playlist']

        formats = []
        quality_key = qualities(('xs', 's', 'm', 'l', 'xl'))

        for format_id, f in playlist.items():
            src = f.get('src')
            if not src:
                continue
            ext = determine_ext(src, None)
            if ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    src + '?hdcore=3.7.0&plugin=aasp-3.7.0.39.44', video_id,
                    f4m_id='hds', fatal=False))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    src, video_id, 'mp4', m3u8_id='hls',
                    entry_protocol='m3u8_native', fatal=False))
            else:
                quality = f.get('quality')
                ff = {
                    'url': src,
                    'format_id': quality or format_id,
                    'quality': quality_key(quality),
                }
                type_ = f.get('type')
                if type_ and type_.split('/')[0] == 'audio':
                    ff['vcodec'] = 'none'
                    ff['ext'] = ext or 'mp3'
                formats.append(ff)
        self._sort_formats(formats)

        config = playlist['config']

        live = playlist.get('config', {}).get('streamType') in ['httpVideoLive', 'httpAudioLive']
        title = config['title']
        if live:
            title = self._live_title(title)
        uploader = ppjson.get('config', {}).get('branding')
        upload_date = ppjson.get('config', {}).get('publicationDate')
        duration = int_or_none(config.get('duration'))

        thumbnails = []
        poster = try_get(config, lambda x: x['poster'], dict) or {}
        for thumbnail_id, thumbnail in poster.items():
            thumbnail_url = urljoin(url, thumbnail.get('src'))
            if not thumbnail_url:
                continue
            thumbnails.append({
                'id': thumbnail.get('quality') or thumbnail_id,
                'url': thumbnail_url,
                'preference': quality_key(thumbnail.get('quality')),
            })

        subtitles = {}
        tracks = config.get('tracks')
        if tracks and isinstance(tracks, list):
            for track in tracks:
                if not isinstance(track, dict):
                    continue
                track_url = urljoin(url, track.get('src'))
                if not track_url:
                    continue
                subtitles.setdefault(track.get('srclang') or 'de', []).append({
                    'url': track_url,
                    'ext': 'ttml',
                })

        return {
            'id': video_id,
            'title': title,
            'is_live': live,
            'uploader': uploader if uploader != '-' else None,
            'upload_date': upload_date[0:8] if upload_date else None,
            'duration': duration,
            'thumbnails': thumbnails,
            'formats': formats,
            'subtitles': subtitles,
        }