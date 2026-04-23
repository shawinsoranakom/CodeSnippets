def _get_formats_and_subtitles(self, info, video_id):
        formats, subtitles = [], {}

        for src in traverse_obj(info, ('src', ..., {dict})):
            format_id = src.get('label')
            src_url = src.get('src')
            if re.match(r'https?:/[^/]', src_url):
                src_url = src_url.replace(':/', '://', 1)
            ext = determine_ext(src_url, mimetype2ext(src.get('type')))

            if not format_id or not src_url:
                continue
            elif format_id == 'hls' or ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src_url, video_id, 'mp4', m3u8_id=format_id, fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)

            elif format_id in self._QUALITIES:
                if src_url.startswith('/mp4:protected/'):
                    # TODO: Correct extraction for these files
                    continue
                formats.append({
                    'url': src_url,
                    'ext': ext,
                    'format_id': format_id,
                    'width': self._QUALITIES[format_id][0],
                    'height': self._QUALITIES[format_id][1],
                })

        return formats, subtitles