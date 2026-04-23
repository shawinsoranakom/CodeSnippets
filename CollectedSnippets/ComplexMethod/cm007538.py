def _real_extract(self, url):
        video_id = self._match_id(url)
        video = self._download_json(
            'https://platform.fusion.net/wp-json/fusiondotnet/v1/video/' + video_id, video_id)

        info = {
            'id': video_id,
            'title': video['title'],
            'description': video.get('excerpt'),
            'timestamp': parse_iso8601(video.get('published')),
            'series': video.get('show'),
        }

        formats = []
        src = video.get('src') or {}
        for f_id, f in src.items():
            for q_id, q in f.items():
                q_url = q.get('url')
                if not q_url:
                    continue
                ext = determine_ext(q_url, mimetype2ext(q.get('type')))
                if ext == 'smil':
                    formats.extend(self._extract_smil_formats(q_url, video_id, fatal=False))
                elif f_id == 'm3u8-variant' or (ext == 'm3u8' and q_id == 'Variant'):
                    formats.extend(self._extract_m3u8_formats(
                        q_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))
                else:
                    formats.append({
                        'format_id': '-'.join([f_id, q_id]),
                        'url': q_url,
                        'width': int_or_none(q.get('width')),
                        'height': int_or_none(q.get('height')),
                        'tbr': int_or_none(self._search_regex(r'_(\d+)\.m(?:p4|3u8)', q_url, 'bitrate')),
                        'ext': 'mp4' if ext == 'm3u8' else ext,
                        'protocol': 'm3u8_native' if ext == 'm3u8' else 'https',
                    })
        if formats:
            self._sort_formats(formats)
            info['formats'] = formats
        else:
            info.update({
                '_type': 'url',
                'url': 'anvato:uni:' + video['video_ids']['anvato'],
                'ie_key': 'Anvato',
            })

        return info