def _entries(self, playlist):
        for item in playlist:
            video_id = item['mediaid']
            thumbnails = [{
                'url': image.get('src'),
                'width': int_or_none(image.get('width')),
            } for image in item.get('images') or []]
            formats, subtitles = [], {}
            for source in item.get('sources') or []:
                if not source.get('file'):
                    continue
                if source.get('type') == 'application/vnd.apple.mpegurl':
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(source['file'], video_id)
                    formats.extend(fmts)
                    subtitles = self._merge_subtitles(subs, subtitles)
                elif source.get('type') == 'audio/mp4':
                    formats.append({
                        'format_id': source.get('label'),
                        'url': source['file'],
                        'vcodec': 'none',
                    })
                else:
                    formats.append({
                        'format_id': source.get('label'),
                        'height': source.get('height'),
                        'width': source.get('width'),
                        'url': source['file'],
                    })
            for track in item.get('tracks'):
                if track.get('kind') == 'captions' and track.get('file'):
                    subtitles.setdefault('en', []).append({
                        'url': track['file'],
                    })
            yield {
                'id': video_id,
                'title': item['title'],
                'description': item.get('description'),
                'thumbnails': thumbnails,
                'thumbnail': item.get('image'),
                'timestamp': item.get('pubdate'),
                'duration': item.get('duration'),
                'formats': formats,
                'subtitles': subtitles,
            }