def _parse_m3u8_formats(self, m3u8_doc, m3u8_url, ext=None,
                            entry_protocol='m3u8', preference=None,
                            m3u8_id=None, live=False):
        if '#EXT-X-FAXS-CM:' in m3u8_doc:  # Adobe Flash Access
            return []

        if re.search(r'#EXT-X-SESSION-KEY:.*?URI="skd://', m3u8_doc):  # Apple FairPlay
            return []

        formats = []

        format_url = lambda u: (
            u
            if re.match(r'^https?://', u)
            else compat_urlparse.urljoin(m3u8_url, u))

        # References:
        # 1. https://tools.ietf.org/html/draft-pantos-http-live-streaming-21
        # 2. https://github.com/ytdl-org/youtube-dl/issues/12211
        # 3. https://github.com/ytdl-org/youtube-dl/issues/18923

        # We should try extracting formats only from master playlists [1, 4.3.4],
        # i.e. playlists that describe available qualities. On the other hand
        # media playlists [1, 4.3.3] should be returned as is since they contain
        # just the media without qualities renditions.
        # Fortunately, master playlist can be easily distinguished from media
        # playlist based on particular tags availability. As of [1, 4.3.3, 4.3.4]
        # master playlist tags MUST NOT appear in a media playlist and vice versa.
        # As of [1, 4.3.3.1] #EXT-X-TARGETDURATION tag is REQUIRED for every
        # media playlist and MUST NOT appear in master playlist thus we can
        # clearly detect media playlist with this criterion.

        if '#EXT-X-TARGETDURATION' in m3u8_doc:  # media playlist, return as is
            return [{
                'url': m3u8_url,
                'format_id': m3u8_id,
                'ext': ext,
                'protocol': entry_protocol,
                'preference': preference,
            }]

        groups = {}
        last_stream_inf = {}

        def extract_media(x_media_line):
            media = parse_m3u8_attributes(x_media_line)
            # As per [1, 4.3.4.1] TYPE, GROUP-ID and NAME are REQUIRED
            media_type, group_id, name = media.get('TYPE'), media.get('GROUP-ID'), media.get('NAME')
            if not (media_type and group_id and name):
                return
            groups.setdefault(group_id, []).append(media)
            if media_type not in ('VIDEO', 'AUDIO'):
                return
            media_url = media.get('URI')
            if media_url:
                format_id = []
                for v in (m3u8_id, group_id, name):
                    if v:
                        format_id.append(v)
                f = {
                    'format_id': '-'.join(format_id),
                    'url': format_url(media_url),
                    'manifest_url': m3u8_url,
                    'language': media.get('LANGUAGE'),
                    'ext': ext,
                    'protocol': entry_protocol,
                    'preference': preference,
                }
                if media_type == 'AUDIO':
                    f['vcodec'] = 'none'
                formats.append(f)

        def build_stream_name():
            # Despite specification does not mention NAME attribute for
            # EXT-X-STREAM-INF tag it still sometimes may be present (see [1]
            # or vidio test in TestInfoExtractor.test_parse_m3u8_formats)
            # 1. http://www.vidio.com/watch/165683-dj_ambred-booyah-live-2015
            stream_name = last_stream_inf.get('NAME')
            if stream_name:
                return stream_name
            # If there is no NAME in EXT-X-STREAM-INF it will be obtained
            # from corresponding rendition group
            stream_group_id = last_stream_inf.get('VIDEO')
            if not stream_group_id:
                return
            stream_group = groups.get(stream_group_id)
            if not stream_group:
                return stream_group_id
            rendition = stream_group[0]
            return rendition.get('NAME') or stream_group_id

        # parse EXT-X-MEDIA tags before EXT-X-STREAM-INF in order to have the
        # chance to detect video only formats when EXT-X-STREAM-INF tags
        # precede EXT-X-MEDIA tags in HLS manifest such as [3].
        for line in m3u8_doc.splitlines():
            if line.startswith('#EXT-X-MEDIA:'):
                extract_media(line)

        for line in m3u8_doc.splitlines():
            if line.startswith('#EXT-X-STREAM-INF:'):
                last_stream_inf = parse_m3u8_attributes(line)
            elif line.startswith('#') or not line.strip():
                continue
            else:
                tbr = float_or_none(
                    last_stream_inf.get('AVERAGE-BANDWIDTH')
                    or last_stream_inf.get('BANDWIDTH'), scale=1000)
                format_id = []
                if m3u8_id:
                    format_id.append(m3u8_id)
                stream_name = build_stream_name()
                # Bandwidth of live streams may differ over time thus making
                # format_id unpredictable. So it's better to keep provided
                # format_id intact.
                if not live:
                    format_id.append(stream_name if stream_name else '%d' % (tbr if tbr else len(formats)))
                manifest_url = format_url(line.strip())
                f = {
                    'format_id': '-'.join(format_id),
                    'url': manifest_url,
                    'manifest_url': m3u8_url,
                    'tbr': tbr,
                    'ext': ext,
                    'fps': float_or_none(last_stream_inf.get('FRAME-RATE')),
                    'protocol': entry_protocol,
                    'preference': preference,
                }
                resolution = last_stream_inf.get('RESOLUTION')
                if resolution:
                    mobj = re.search(r'(?P<width>\d+)[xX](?P<height>\d+)', resolution)
                    if mobj:
                        f['width'] = int(mobj.group('width'))
                        f['height'] = int(mobj.group('height'))
                # Unified Streaming Platform
                mobj = re.search(
                    r'audio.*?(?:%3D|=)(\d+)(?:-video.*?(?:%3D|=)(\d+))?', f['url'])
                if mobj:
                    abr, vbr = mobj.groups()
                    abr, vbr = float_or_none(abr, 1000), float_or_none(vbr, 1000)
                    f.update({
                        'vbr': vbr,
                        'abr': abr,
                    })
                codecs = parse_codecs(last_stream_inf.get('CODECS'))
                f.update(codecs)
                audio_group_id = last_stream_inf.get('AUDIO')
                # As per [1, 4.3.4.1.1] any EXT-X-STREAM-INF tag which
                # references a rendition group MUST have a CODECS attribute.
                # However, this is not always respected, for example, [2]
                # contains EXT-X-STREAM-INF tag which references AUDIO
                # rendition group but does not have CODECS and despite
                # referencing an audio group it represents a complete
                # (with audio and video) format. So, for such cases we will
                # ignore references to rendition groups and treat them
                # as complete formats.
                if audio_group_id and codecs and f.get('vcodec') != 'none':
                    audio_group = groups.get(audio_group_id)
                    if audio_group and audio_group[0].get('URI'):
                        # TODO: update acodec for audio only formats with
                        # the same GROUP-ID
                        f['acodec'] = 'none'
                formats.append(f)

                # for DailyMotion
                progressive_uri = last_stream_inf.get('PROGRESSIVE-URI')
                if progressive_uri:
                    http_f = f.copy()
                    del http_f['manifest_url']
                    http_f.update({
                        'format_id': f['format_id'].replace('hls-', 'http-'),
                        'protocol': 'http',
                        'url': progressive_uri,
                    })
                    formats.append(http_f)

                last_stream_inf = {}
        return formats