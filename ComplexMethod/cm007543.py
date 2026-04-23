def _extract_theplatform_smil(self, smil_url, video_id, note='Downloading SMIL data'):
        meta = self._download_xml(
            smil_url, video_id, note=note, query={'format': 'SMIL'},
            headers=self.geo_verification_headers())
        error_element = find_xpath_attr(meta, _x('.//smil:ref'), 'src')
        if error_element is not None:
            exception = find_xpath_attr(
                error_element, _x('.//smil:param'), 'name', 'exception')
            if exception is not None:
                if exception.get('value') == 'GeoLocationBlocked':
                    self.raise_geo_restricted(error_element.attrib['abstract'])
                elif error_element.attrib['src'].startswith(
                        'http://link.theplatform.%s/s/errorFiles/Unavailable.'
                        % self._TP_TLD):
                    raise ExtractorError(
                        error_element.attrib['abstract'], expected=True)

        smil_formats = self._parse_smil_formats(
            meta, smil_url, video_id, namespace=default_ns,
            # the parameters are from syfy.com, other sites may use others,
            # they also work for nbc.com
            f4m_params={'g': 'UXWGVKRWHFSP', 'hdcore': '3.0.3'},
            transform_rtmp_url=lambda streamer, src: (streamer, 'mp4:' + src))

        formats = []
        for _format in smil_formats:
            if OnceIE.suitable(_format['url']):
                formats.extend(self._extract_once_formats(_format['url']))
            else:
                media_url = _format['url']
                if determine_ext(media_url) == 'm3u8':
                    hdnea2 = self._get_cookies(media_url).get('hdnea2')
                    if hdnea2:
                        _format['url'] = update_url_query(media_url, {'hdnea3': hdnea2.value})

                formats.append(_format)

        subtitles = self._parse_smil_subtitles(meta, default_ns)

        return formats, subtitles