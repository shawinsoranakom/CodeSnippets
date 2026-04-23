def _real_extract(self, url):
        bu, media_type, media_id = re.match(self._VALID_URL, url).groups()
        media_data = self._get_media_data(bu, media_type, media_id)
        title = media_data['title']

        formats = []
        q = qualities(['SD', 'HD'])
        for source in (media_data.get('resourceList') or []):
            format_url = source.get('url')
            if not format_url:
                continue
            protocol = source.get('protocol')
            quality = source.get('quality')
            format_id = []
            for e in (protocol, source.get('encoding'), quality):
                if e:
                    format_id.append(e)
            format_id = '-'.join(format_id)

            if protocol in ('HDS', 'HLS'):
                if source.get('tokenType') == 'AKAMAI':
                    format_url = self._get_tokenized_src(
                        format_url, media_id, format_id)
                    formats.extend(self._extract_akamai_formats(
                        format_url, media_id))
                elif protocol == 'HLS':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, media_id, 'mp4', 'm3u8_native',
                        m3u8_id=format_id, fatal=False))
            elif protocol in ('HTTP', 'HTTPS'):
                formats.append({
                    'format_id': format_id,
                    'url': format_url,
                    'quality': q(quality),
                })

        # This is needed because for audio medias the podcast url is usually
        # always included, even if is only an audio segment and not the
        # whole episode.
        if int_or_none(media_data.get('position')) == 0:
            for p in ('S', 'H'):
                podcast_url = media_data.get('podcast%sdUrl' % p)
                if not podcast_url:
                    continue
                quality = p + 'D'
                formats.append({
                    'format_id': 'PODCAST-' + quality,
                    'url': podcast_url,
                    'quality': q(quality),
                })
        self._sort_formats(formats)

        subtitles = {}
        if media_type == 'video':
            for sub in (media_data.get('subtitleList') or []):
                sub_url = sub.get('url')
                if not sub_url:
                    continue
                lang = sub.get('locale') or self._DEFAULT_LANGUAGE_CODES[bu]
                subtitles.setdefault(lang, []).append({
                    'url': sub_url,
                })

        return {
            'id': media_id,
            'title': title,
            'description': media_data.get('description'),
            'timestamp': parse_iso8601(media_data.get('date')),
            'thumbnail': media_data.get('imageUrl'),
            'duration': float_or_none(media_data.get('duration'), 1000),
            'subtitles': subtitles,
            'formats': formats,
        }