def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        display_id = mobj.group('id')

        player_url = mobj.group('mainurl') + '~playerXml.xml'
        doc = self._download_xml(player_url, display_id)
        video_node = doc.find('./video')
        upload_date = unified_strdate(xpath_text(
            video_node, './broadcastDate'))
        thumbnail = xpath_text(video_node, './/teaserImage//variant/url')

        formats = []
        for a in video_node.findall('.//asset'):
            file_name = xpath_text(a, './fileName', default=None)
            if not file_name:
                continue
            format_type = a.attrib.get('type')
            format_url = url_or_none(file_name)
            if format_url:
                ext = determine_ext(file_name)
                if ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, display_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id=format_type or 'hls', fatal=False))
                    continue
                elif ext == 'f4m':
                    formats.extend(self._extract_f4m_formats(
                        update_url_query(format_url, {'hdcore': '3.7.0'}),
                        display_id, f4m_id=format_type or 'hds', fatal=False))
                    continue
            f = {
                'format_id': format_type,
                'width': int_or_none(xpath_text(a, './frameWidth')),
                'height': int_or_none(xpath_text(a, './frameHeight')),
                'vbr': int_or_none(xpath_text(a, './bitrateVideo')),
                'abr': int_or_none(xpath_text(a, './bitrateAudio')),
                'vcodec': xpath_text(a, './codecVideo'),
                'tbr': int_or_none(xpath_text(a, './totalBitrate')),
            }
            server_prefix = xpath_text(a, './serverPrefix', default=None)
            if server_prefix:
                f.update({
                    'url': server_prefix,
                    'playpath': file_name,
                })
            else:
                if not format_url:
                    continue
                f['url'] = format_url
            formats.append(f)

        _SUB_FORMATS = (
            ('./dataTimedText', 'ttml'),
            ('./dataTimedTextNoOffset', 'ttml'),
            ('./dataTimedTextVtt', 'vtt'),
        )

        subtitles = {}
        for subsel, subext in _SUB_FORMATS:
            for node in video_node.findall(subsel):
                subtitles.setdefault('de', []).append({
                    'url': node.attrib['url'],
                    'ext': subext,
                })

        return {
            'id': xpath_text(video_node, './videoId', default=display_id),
            'formats': formats,
            'subtitles': subtitles,
            'display_id': display_id,
            'title': video_node.find('./title').text,
            'duration': parse_duration(video_node.find('./duration').text),
            'upload_date': upload_date,
            'thumbnail': thumbnail,
        }