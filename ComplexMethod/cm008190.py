def _real_extract(self, url):
        video_id = self._match_id(url)

        if url.startswith('wdr:'):
            video_id = url[4:]
            url = self._asset_url(video_id)

        metadata = self._download_json(
            url, video_id, transform_source=strip_jsonp)

        is_live = metadata.get('mediaType') == 'live'

        tracker_data = metadata['trackerData']
        title = tracker_data['trackerClipTitle']
        media_resource = metadata['mediaResource']

        formats = []
        subtitles = {}

        # check if the metadata contains a direct URL to a file
        for kind, media in media_resource.items():
            if kind == 'captionsHash':
                for ext, url in media.items():
                    subtitles.setdefault('de', []).append({
                        'url': url,
                        'ext': ext,
                    })
                continue

            if kind not in ('dflt', 'alt'):
                continue
            if not isinstance(media, dict):
                continue

            for tag_name, medium_url in media.items():
                if tag_name not in ('videoURL', 'audioURL'):
                    continue

                ext = determine_ext(medium_url)
                if ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        medium_url, video_id, 'mp4', 'm3u8_native',
                        m3u8_id='hls'))
                elif ext == 'f4m':
                    manifest_url = update_url_query(
                        medium_url, {'hdcore': '3.2.0', 'plugin': 'aasp-3.2.0.77.18'})
                    formats.extend(self._extract_f4m_formats(
                        manifest_url, video_id, f4m_id='hds', fatal=False))
                elif ext == 'smil':
                    formats.extend(self._extract_smil_formats(
                        medium_url, 'stream', fatal=False))
                else:
                    a_format = {
                        'url': medium_url,
                    }
                    if ext == 'unknown_video':
                        urlh = self._request_webpage(
                            medium_url, video_id, note='Determining extension')
                        ext = urlhandle_detect_ext(urlh)
                        a_format['ext'] = ext
                    formats.append(a_format)

        caption_url = media_resource.get('captionURL')
        if caption_url:
            subtitles['de'] = [{
                'url': caption_url,
                'ext': 'ttml',
            }]
        captions_hash = media_resource.get('captionsHash')
        if isinstance(captions_hash, dict):
            for ext, format_url in captions_hash.items():
                format_url = url_or_none(format_url)
                if not format_url:
                    continue
                subtitles.setdefault('de', []).append({
                    'url': format_url,
                    'ext': determine_ext(format_url, None) or ext,
                })

        return {
            'id': tracker_data.get('trackerClipId', video_id),
            'title': title,
            'alt_title': tracker_data.get('trackerClipSubcategory'),
            'formats': formats,
            'subtitles': subtitles,
            'upload_date': unified_strdate(tracker_data.get('trackerClipAirTime')),
            'is_live': is_live,
        }