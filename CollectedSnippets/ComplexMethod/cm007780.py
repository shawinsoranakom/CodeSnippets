def _extract_video_formats(self, mdoc, mtvn_id, video_id):
        if re.match(r'.*/(error_country_block\.swf|geoblock\.mp4|copyright_error\.flv(?:\?geo\b.+?)?)$', mdoc.find('.//src').text) is not None:
            if mtvn_id is not None and self._MOBILE_TEMPLATE is not None:
                self.to_screen('The normal version is not available from your '
                               'country, trying with the mobile version')
                return self._extract_mobile_video_formats(mtvn_id)
            raise ExtractorError('This video is not available from your country.',
                                 expected=True)

        formats = []
        for rendition in mdoc.findall('.//rendition'):
            if rendition.get('method') == 'hls':
                hls_url = rendition.find('./src').text
                formats.extend(self._extract_m3u8_formats(
                    hls_url, video_id, ext='mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                # fms
                try:
                    _, _, ext = rendition.attrib['type'].partition('/')
                    rtmp_video_url = rendition.find('./src').text
                    if 'error_not_available.swf' in rtmp_video_url:
                        raise ExtractorError(
                            '%s said: video is not available' % self.IE_NAME,
                            expected=True)
                    if rtmp_video_url.endswith('siteunavail.png'):
                        continue
                    formats.extend([{
                        'ext': 'flv' if rtmp_video_url.startswith('rtmp') else ext,
                        'url': rtmp_video_url,
                        'format_id': '-'.join(filter(None, [
                            'rtmp' if rtmp_video_url.startswith('rtmp') else None,
                            rendition.get('bitrate')])),
                        'width': int(rendition.get('width')),
                        'height': int(rendition.get('height')),
                    }])
                except (KeyError, TypeError):
                    raise ExtractorError('Invalid rendition field.')
        if formats:
            self._sort_formats(formats)
        return formats