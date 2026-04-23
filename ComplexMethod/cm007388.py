def _extract_format(self, video_id, formats, format_urls, meta):
        format_url = url_or_none(meta.get('url'))
        if not format_url:
            return
        if format_url in format_urls:
            return
        format_urls.add(format_url)
        mime_type = meta.get('mimeType')
        ext = determine_ext(format_url)

        join_nonempty = lambda s, l: s.join(filter(None, l))
        meta_map = lambda t: map(lambda x: str_or_none(meta.get(x)), t)

        if mime_type == 'application/x-mpegURL' or ext == 'm3u8':
            new_formats = self._extract_m3u8_formats(
                format_url, video_id, 'mp4', m3u8_id='hls',
                entry_protocol='m3u8_native', fatal=False)
        elif mime_type == 'application/f4m+xml' or ext == 'f4m':
            new_formats = self._extract_f4m_formats(
                update_url_query(format_url, {'hdcore': '3.7.0'}), video_id, f4m_id='hds', fatal=False)
        else:
            f = parse_codecs(meta.get('mimeCodec'))
            if not f:
                data = meta.get('type', '').split('_')
                if try_get(data, lambda x: x[2]) == ext:
                    f = dict(zip(('vcodec', 'acodec'), data[1]))

            format_id = ['http']
            format_id.extend(join_nonempty('-', meta_map(('type', 'quality'))))
            f.update({
                'url': format_url,
                'format_id': '-'.join(format_id),
                'tbr': int_or_none(self._search_regex(r'_(\d+)k_', format_url, 'tbr', default=None))
            })
            new_formats = [f]

        formats.extend(merge_dicts(f, {
            'format_note': join_nonempty(',', meta_map(('quality', 'class'))),
            'language': meta.get('language'),
            'language_preference': 10 if meta.get('class') == 'main' else -10 if meta.get('class') == 'ad' else -1,
            'quality': qualities(self._QUALITIES)(meta.get('quality')),
        }) for f in new_formats)