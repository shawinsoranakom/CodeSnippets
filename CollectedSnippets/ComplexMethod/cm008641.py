def _real_extract(self, url):
        channel, video_id = self._match_valid_url(url).group('site', 'id')
        webpage = self._download_webpage(url, video_id)

        nbc_data = self._search_json(
            r'(?:<script>\s*var\s+nbc\s*=|Object\.assign\(nbc,)', webpage, 'NBC JSON data', video_id)
        pdk_acct = nbc_data.get('pdkAcct') or 'Yh1nAC'
        fw_ssid = traverse_obj(nbc_data, ('video', 'fwSSID'))

        video_data = self._search_json(
            r'data-videos="\[', webpage, 'video data', video_id, default={}, transform_source=unescapeHTML)
        video_data.update(self._search_json(
            r'data-meta="', webpage, 'metadata', video_id, default={}, transform_source=unescapeHTML))
        if not video_data:
            raise ExtractorError('No video metadata found in webpage', expected=True)

        info, formats = {}, []
        is_live = int_or_none(video_data.get('mpx_is_livestream')) == 1
        query = {
            'formats': 'MPEG-DASH none,M3U none,MPEG-DASH none,MPEG4,MP3',
            'format': 'SMIL',
            'fwsitesection': fw_ssid,
            'fwNetworkID': traverse_obj(nbc_data, ('video', 'fwNetworkID'), default='382114'),
            'pprofile': 'ots_desktop_html',
            'sensitive': 'false',
            'w': '1920',
            'h': '1080',
            'mode': 'LIVE' if is_live else 'on-demand',
            'vpaid': 'script',
            'schema': '2.0',
            'sdk': 'PDK 6.1.3',
        }

        if is_live:
            player_id = traverse_obj(video_data, ((None, ('video', 'meta')), (
                'mpx_m3upid', 'mpx_pid', 'pid_streaming_web_medium')), get_all=False)
            info['title'] = f'{channel} livestream'

        else:
            player_id = traverse_obj(video_data, (
                (None, ('video', 'meta')), ('pid_streaming_web_high', 'mpx_pid')), get_all=False)

            date_string = traverse_obj(video_data, 'date_string', 'date_gmt')
            if date_string:
                date_string = self._search_regex(
                    r'datetime="([^"]+)"', date_string, 'date string', fatal=False)
            else:
                date_string = traverse_obj(
                    nbc_data, ('dataLayer', 'adobe', ('prop70', 'eVar70', 'eVar59')), get_all=False)

            video_url = traverse_obj(video_data, ((None, ('video', 'meta')), 'mp4_url'), get_all=False)
            if video_url:
                ext = determine_ext(video_url)
                height = self._search_regex(r'\d+-(\d+)p', url_basename(video_url), 'height', default=None)
                formats.append({
                    'url': video_url,
                    'ext': ext,
                    'width': int_or_none(self._RESOLUTIONS.get(height)),
                    'height': int_or_none(height),
                    'format_id': f'http-{ext}',
                })

            info.update({
                'title': video_data.get('title') or traverse_obj(nbc_data, (
                    'dataLayer', (None, 'adobe'), ('contenttitle', 'title', 'prop22')), get_all=False),
                'description':
                    traverse_obj(video_data, 'summary', 'excerpt', 'video_hero_text')
                    or clean_html(traverse_obj(nbc_data, ('dataLayer', 'summary'))),
                'timestamp': unified_timestamp(date_string),
            })

        smil = None
        if player_id and fw_ssid:
            smil = self._download_xml(
                f'https://link.theplatform.com/s/{pdk_acct}/{player_id}', video_id,
                note='Downloading SMIL data', query=query, fatal=is_live)
            if not isinstance(smil, xml.etree.ElementTree.Element):
                smil = None
        subtitles = self._parse_smil_subtitles(smil, default_ns) if smil is not None else {}
        for video in smil.findall(self._xpath_ns('.//video', default_ns)) if smil is not None else []:
            info['duration'] = float_or_none(remove_end(video.get('dur'), 'ms'), 1000)
            video_src_url = video.get('src')
            ext = mimetype2ext(video.get('type'), default=determine_ext(video_src_url))
            if ext == 'm3u8':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    video_src_url, video_id, 'mp4', m3u8_id='hls', fatal=is_live,
                    live=is_live, errnote='No HLS formats found')
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif video_src_url:
                formats.append({
                    'url': video_src_url,
                    'format_id': f'https-{ext}',
                    'ext': ext,
                    'width': int_or_none(video.get('width')),
                    'height': int_or_none(video.get('height')),
                })

        if not formats:
            self.raise_no_formats('No video content found in webpage', expected=True)
        elif is_live:
            try:
                self._request_webpage(
                    HEADRequest(formats[0]['url']), video_id, note='Checking live status')
            except ExtractorError:
                raise UserNotLive(video_id=channel)

        return {
            'id': video_id,
            'channel': channel,
            'channel_id': nbc_data.get('callLetters'),
            'uploader': nbc_data.get('on_air_name'),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
            **info,
        }