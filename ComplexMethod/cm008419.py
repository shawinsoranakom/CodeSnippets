def _extract_relinker_info(self, relinker_url, video_id, audio_only=False):
        def fix_cdata(s):
            # remove \r\n\t before and after <![CDATA[ ]]> to avoid
            # polluted text with xpath_text
            s = re.sub(r'(\]\]>)[\r\n\t]+(</)', '\\1\\2', s)
            return re.sub(r'(>)[\r\n\t]+(<!\[CDATA\[)', '\\1\\2', s)

        if not re.match(r'https?://', relinker_url):
            return {'formats': [{'url': relinker_url}]}

        # set User-Agent to generic 'Rai' to avoid quality filtering from
        # the media server and get the maximum qualities available
        relinker = self._download_xml(
            relinker_url, video_id, note='Downloading XML metadata',
            transform_source=fix_cdata, query={'output': 64},
            headers={**self.geo_verification_headers(), 'User-Agent': 'Rai'})

        if xpath_text(relinker, './license_url', default='{}') != '{}':
            self.report_drm(video_id)

        is_live = xpath_text(relinker, './is_live', default='N') == 'Y'
        duration = parse_duration(xpath_text(relinker, './duration', default=None))
        media_url = xpath_text(relinker, './url[@type="content"]', default=None)

        if not media_url:
            self.raise_no_formats('The relinker returned no media url')

        # geo flag is a bit unreliable and not properly set all the time
        geoprotection = xpath_text(relinker, './geoprotection', default='N') == 'Y'

        ext = determine_ext(media_url).lower()
        formats = []

        if ext == 'mp3':
            formats.append({
                'url': media_url,
                'vcodec': 'none',
                'acodec': 'mp3',
                'format_id': 'https-mp3',
            })
        elif ext == 'm3u8' or 'format=m3u8' in media_url:
            formats.extend(self._fix_m3u8_formats(media_url, video_id))
        elif ext == 'f4m':
            # very likely no longer needed. Cannot find any url that uses it.
            manifest_url = update_url_query(
                media_url.replace('manifest#live_hds.f4m', 'manifest.f4m'),
                {'hdcore': '3.7.0', 'plugin': 'aasp-3.7.0.39.44'})
            formats.extend(self._extract_f4m_formats(
                manifest_url, video_id, f4m_id='hds', fatal=False))
        elif ext == 'mp4':
            bitrate = int_or_none(xpath_text(relinker, './bitrate'))
            formats.append({
                'url': media_url,
                'tbr': bitrate if bitrate > 0 else None,
                'format_id': join_nonempty('https', bitrate, delim='-'),
            })
        else:
            raise ExtractorError(f'Unrecognized media extension "{ext}"')

        if (not formats and geoprotection is True) or '/video_no_available.mp4' in media_url:
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES, metadata_available=True)

        if not audio_only and not is_live:
            formats.extend(self._create_http_urls(media_url, relinker_url, formats, video_id))

        return filter_dict({
            'is_live': is_live,
            'duration': duration,
            'formats': formats,
        })