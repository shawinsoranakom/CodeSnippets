def _extract_info(self, app_code, video_id):
        metas = self._call_api('meta/v1/index.ashx', video_id, app_code)['Metas']

        def get_meta(name):
            for meta in metas:
                if meta.get('name') == name:
                    text = meta.get('text')
                    if text:
                        return text

        # protectionType does not necessarily mean the video is DRM protected (see
        # https://github.com/ytdl-org/youtube-dl/pull/18609).
        if get_meta('protectionType'):
            self.report_warning('This video is probably DRM protected.')

        query = {
            'connectionType': 'hd',
            'deviceType': 'ipad',
            'multibitrate': 'true',
        }
        if self._claims:
            query['claims'] = self._claims
        v_data = self._call_api('validation/v2/', video_id, app_code, query)
        v_url = v_data.get('url')
        if not v_url:
            error = v_data['message']
            if error == "Le contenu sélectionné n'est pas disponible dans votre pays":
                raise self.raise_geo_restricted(error, self._GEO_COUNTRIES)
            if error == 'Le contenu sélectionné est disponible seulement en premium':
                self.raise_login_required(error)
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, error), expected=True)
        formats = self._extract_m3u8_formats(v_url, video_id, 'mp4')
        self._sort_formats(formats)

        subtitles = {}
        closed_caption_url = get_meta('closedCaption') or get_meta('closedCaptionHTML5')
        if closed_caption_url:
            subtitles['fr'] = [{
                'url': closed_caption_url,
                'ext': determine_ext(closed_caption_url, 'vtt'),
            }]

        return {
            'id': video_id,
            'title': get_meta('Title') or get_meta('AV-nomEmission'),
            'description': get_meta('Description') or get_meta('ShortDescription'),
            'thumbnail': get_meta('imageHR') or get_meta('imageMR') or get_meta('imageBR'),
            'duration': int_or_none(get_meta('length')),
            'series': get_meta('Emission'),
            'season_number': int_or_none('SrcSaison'),
            'episode_number': int_or_none('SrcEpisode'),
            'upload_date': unified_strdate(get_meta('Date')),
            'subtitles': subtitles,
            'formats': formats,
        }