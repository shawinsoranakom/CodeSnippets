def _real_extract(self, url):
        display_id = self._match_id(url)
        video = self._download_video_data(display_id)
        video_id = video['id']
        title = video['title']
        feed = self._get_feed(video)

        formats = []
        for playback in (feed.get('playbacks') or []):
            playback_url = playback.get('url')
            if not playback_url:
                continue
            name = playback.get('name')
            ext = determine_ext(playback_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    playback_url, video_id, 'mp4',
                    'm3u8_native', m3u8_id=name, fatal=False))
            else:
                f = {
                    'format_id': name,
                    'url': playback_url,
                }
                mobj = re.search(r'_(\d+)K_(\d+)X(\d+)', name)
                if mobj:
                    f.update({
                        'height': int(mobj.group(3)),
                        'tbr': int(mobj.group(1)),
                        'width': int(mobj.group(2)),
                    })
                mobj = re.search(r'_(\d+)x(\d+)_(\d+)_(\d+)K\.mp4', playback_url)
                if mobj:
                    f.update({
                        'fps': int(mobj.group(3)),
                        'height': int(mobj.group(2)),
                        'tbr': int(mobj.group(4)),
                        'width': int(mobj.group(1)),
                    })
                formats.append(f)

        thumbnails = []
        for cut in (try_get(feed, lambda x: x['image']['cuts'], list) or []):
            src = cut.get('src')
            if not src:
                continue
            thumbnails.append({
                'height': int_or_none(cut.get('height')),
                'url': src,
                'width': int_or_none(cut.get('width')),
            })

        language = (video.get('language') or 'EN').lower()

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': video.get('description'),
            'duration': parse_duration(feed.get('duration')),
            'thumbnails': thumbnails,
            'timestamp': parse_iso8601(video.get(self._TIMESTAMP_KEY)),
            'subtitles': self._extract_mlb_subtitles(feed, language),
        }