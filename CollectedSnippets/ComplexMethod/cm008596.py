def _real_extract(self, url):
        media_type, media_id = self._match_valid_url(url).group('type', 'id')

        media = self._download_json(
            'http://api-media.3cat.cat/pvideo/media.jsp', media_id, query={
                'media': media_type,
                'idint': media_id,
                'format': 'dm',
            })

        formats = []
        media_url = media['media']['url']
        if isinstance(media_url, list):
            for format_ in media_url:
                format_url = url_or_none(format_.get('file'))
                if not format_url:
                    continue
                if determine_ext(format_url) == 'mpd':
                    formats.extend(self._extract_mpd_formats(
                        format_url, media_id, mpd_id='dash', fatal=False))
                    continue
                label = format_.get('label')
                f = parse_resolution(label)
                f.update({
                    'url': format_url,
                    'format_id': label,
                })
                formats.append(f)
        else:
            formats.append({
                'url': media_url,
                'vcodec': 'none' if media_type == 'audio' else None,
            })

        informacio = media['informacio']
        title = informacio['titol']
        durada = informacio.get('durada') or {}
        duration = int_or_none(durada.get('milisegons'), 1000) or parse_duration(durada.get('text'))
        tematica = try_get(informacio, lambda x: x['tematica']['text'])

        data_utc = try_get(informacio, lambda x: x['data_emissio']['utc'])
        timestamp = unified_timestamp(data_utc)

        subtitles = {}
        subtitols = media.get('subtitols') or []
        if isinstance(subtitols, dict):
            subtitols = [subtitols]
        for st in subtitols:
            sub_url = st.get('url')
            if sub_url:
                subtitles.setdefault(
                    st.get('iso') or st.get('text') or 'ca', []).append({
                        'url': sub_url,
                    })

        thumbnails = []
        imatges = media.get('imatges', {})
        if imatges:
            thumbnail_url = imatges.get('url')
            if thumbnail_url:
                thumbnails = [{
                    'url': thumbnail_url,
                    'width': int_or_none(imatges.get('amplada')),
                    'height': int_or_none(imatges.get('alcada')),
                }]

        age_limit = None
        codi_etic = try_get(informacio, lambda x: x['codi_etic']['id'])
        if codi_etic:
            codi_etic_s = codi_etic.split('_')
            if len(codi_etic_s) == 2:
                if codi_etic_s[1] == 'TP':
                    age_limit = 0
                else:
                    age_limit = int_or_none(codi_etic_s[1])

        return {
            'id': media_id,
            'title': title,
            'description': clean_html(informacio.get('descripcio')),
            'duration': duration,
            'timestamp': timestamp,
            'thumbnails': thumbnails,
            'subtitles': subtitles,
            'formats': formats,
            'age_limit': age_limit,
            'alt_title': informacio.get('titol_complet'),
            'episode_number': int_or_none(informacio.get('capitol')),
            'categories': [tematica] if tematica else None,
            'series': informacio.get('programa'),
        }