def _parse_mpd_formats_and_subtitles(
            self, mpd_doc, mpd_id=None, mpd_base_url='', mpd_url=None):
        """
        Parse formats from MPD manifest.
        References:
         1. MPEG-DASH Standard, ISO/IEC 23009-1:2014(E),
            http://standards.iso.org/ittf/PubliclyAvailableStandards/c065274_ISO_IEC_23009-1_2014.zip
         2. https://en.wikipedia.org/wiki/Dynamic_Adaptive_Streaming_over_HTTP
        """
        # TODO: param not yet implemented: default like previous yt-dl logic
        if not self.get_param('dynamic_mpd', False):
            if mpd_doc.get('type') == 'dynamic':
                return [], {}

        namespace = self._search_regex(r'(?i)^{([^}]+)?}MPD$', mpd_doc.tag, 'namespace', default=None)

        def _add_ns(path):
            return self._xpath_ns(path, namespace)

        def is_drm_protected(element):
            return element.find(_add_ns('ContentProtection')) is not None

        from ..utils import YoutubeDLHandler
        fix_path = YoutubeDLHandler._fix_path

        def resolve_base_url(element, parent_base_url=None):
            # TODO: use native XML traversal when ready
            b_url = traverse_obj(element, (
                T(lambda e: e.find(_add_ns('BaseURL')).text)))
            if parent_base_url and b_url:
                if not parent_base_url[-1] in ('/', ':'):
                    parent_base_url += '/'
                b_url = compat_urlparse.urljoin(parent_base_url, b_url)
            if b_url:
                b_url = fix_path(b_url)
            return b_url or parent_base_url

        def extract_multisegment_info(element, ms_parent_info):
            ms_info = ms_parent_info.copy()
            base_url = ms_info['base_url'] = resolve_base_url(element, ms_info.get('base_url'))

            # As per [1, 5.3.9.2.2] SegmentList and SegmentTemplate share some
            # common attributes and elements.  We will only extract relevant
            # for us.
            def extract_common(source):
                segment_timeline = source.find(_add_ns('SegmentTimeline'))
                if segment_timeline is not None:
                    s_e = segment_timeline.findall(_add_ns('S'))
                    if s_e:
                        ms_info['total_number'] = 0
                        ms_info['s'] = []
                        for s in s_e:
                            r = int(s.get('r', 0))
                            ms_info['total_number'] += 1 + r
                            ms_info['s'].append({
                                't': int(s.get('t', 0)),
                                # @d is mandatory (see [1, 5.3.9.6.2, Table 17, page 60])
                                'd': int(s.attrib['d']),
                                'r': r,
                            })
                start_number = source.get('startNumber')
                if start_number:
                    ms_info['start_number'] = int(start_number)
                timescale = source.get('timescale')
                if timescale:
                    ms_info['timescale'] = int(timescale)
                segment_duration = source.get('duration')
                if segment_duration:
                    ms_info['segment_duration'] = float(segment_duration)

            def extract_Initialization(source):
                initialization = source.find(_add_ns('Initialization'))
                if initialization is not None:
                    ms_info['initialization_url'] = initialization.get('sourceURL') or base_url
                    initialization_url_range = initialization.get('range')
                    if initialization_url_range:
                        ms_info['initialization_url_range'] = initialization_url_range

            segment_list = element.find(_add_ns('SegmentList'))
            if segment_list is not None:
                extract_common(segment_list)
                extract_Initialization(segment_list)
                segment_urls_e = segment_list.findall(_add_ns('SegmentURL'))
                segment_urls = traverse_obj(segment_urls_e, (
                    Ellipsis, T(lambda e: e.attrib), 'media'))
                if segment_urls:
                    ms_info['segment_urls'] = segment_urls
                segment_urls_range = traverse_obj(segment_urls_e, (
                    Ellipsis, T(lambda e: e.attrib), 'mediaRange',
                    T(lambda r: re.findall(r'^\d+-\d+$', r)), 0))
                if segment_urls_range:
                    ms_info['segment_urls_range'] = segment_urls_range
                    if not segment_urls:
                        ms_info['segment_urls'] = [base_url for _ in segment_urls_range]
            else:
                segment_template = element.find(_add_ns('SegmentTemplate'))
                if segment_template is not None:
                    extract_common(segment_template)
                    media = segment_template.get('media')
                    if media:
                        ms_info['media'] = media
                    initialization = segment_template.get('initialization')
                    if initialization:
                        ms_info['initialization'] = initialization
                    else:
                        extract_Initialization(segment_template)
            return ms_info

        mpd_duration = parse_duration(mpd_doc.get('mediaPresentationDuration'))
        formats, subtitles = [], {}
        stream_numbers = collections.defaultdict(int)
        mpd_base_url = resolve_base_url(mpd_doc, mpd_base_url or mpd_url)
        for period in mpd_doc.findall(_add_ns('Period')):
            period_duration = parse_duration(period.get('duration')) or mpd_duration
            period_ms_info = extract_multisegment_info(period, {
                'start_number': 1,
                'timescale': 1,
                'base_url': mpd_base_url,
            })
            for adaptation_set in period.findall(_add_ns('AdaptationSet')):
                if is_drm_protected(adaptation_set):
                    continue
                adaptation_set_ms_info = extract_multisegment_info(adaptation_set, period_ms_info)
                for representation in adaptation_set.findall(_add_ns('Representation')):
                    if is_drm_protected(representation):
                        continue
                    representation_attrib = adaptation_set.attrib.copy()
                    representation_attrib.update(representation.attrib)
                    # According to [1, 5.3.7.2, Table 9, page 41], @mimeType is mandatory
                    mime_type = representation_attrib['mimeType']
                    content_type = representation_attrib.get('contentType') or mime_type.split('/')[0]
                    codec_str = representation_attrib.get('codecs', '')
                    # Some kind of binary subtitle found in some youtube livestreams
                    if mime_type == 'application/x-rawcc':
                        codecs = {'scodec': codec_str}
                    else:
                        codecs = parse_codecs(codec_str)
                    if content_type not in ('video', 'audio', 'text'):
                        if mime_type == 'image/jpeg':
                            content_type = mime_type
                        elif codecs.get('vcodec', 'none') != 'none':
                            content_type = 'video'
                        elif codecs.get('acodec', 'none') != 'none':
                            content_type = 'audio'
                        elif codecs.get('scodec', 'none') != 'none':
                            content_type = 'text'
                        elif mimetype2ext(mime_type) in ('tt', 'dfxp', 'ttml', 'xml', 'json'):
                            content_type = 'text'
                        else:
                            self.report_warning('Unknown MIME type %s in DASH manifest' % mime_type)
                            continue

                    representation_id = representation_attrib.get('id')
                    lang = representation_attrib.get('lang')
                    url_el = representation.find(_add_ns('BaseURL'))
                    filesize = int_or_none(url_el.get('{http://youtube.com/yt/2012/10/10}contentLength') if url_el is not None else None)
                    bandwidth = int_or_none(representation_attrib.get('bandwidth'))
                    format_id = join_nonempty(representation_id or content_type, mpd_id)
                    if content_type in ('video', 'audio'):
                        f = {
                            'format_id': '%s-%s' % (mpd_id, representation_id) if mpd_id else representation_id,
                            'manifest_url': mpd_url,
                            'ext': mimetype2ext(mime_type),
                            'width': int_or_none(representation_attrib.get('width')),
                            'height': int_or_none(representation_attrib.get('height')),
                            'tbr': float_or_none(bandwidth, 1000),
                            'asr': int_or_none(representation_attrib.get('audioSamplingRate')),
                            'fps': int_or_none(representation_attrib.get('frameRate')),
                            'language': lang if lang not in ('mul', 'und', 'zxx', 'mis') else None,
                            'format_note': 'DASH %s' % content_type,
                            'filesize': filesize,
                            'container': mimetype2ext(mime_type) + '_dash',
                        }
                        f.update(codecs)
                    elif content_type == 'text':
                        f = {
                            'ext': mimetype2ext(mime_type),
                            'manifest_url': mpd_url,
                            'filesize': filesize,
                        }
                    elif content_type == 'image/jpeg':
                        # See test case in VikiIE
                        # https://www.viki.com/videos/1175236v-choosing-spouse-by-lottery-episode-1
                        f = {
                            'format_id': format_id,
                            'ext': 'mhtml',
                            'manifest_url': mpd_url,
                            'format_note': 'DASH storyboards (jpeg)',
                            'acodec': 'none',
                            'vcodec': 'none',
                        }
                    if is_drm_protected(adaptation_set) or is_drm_protected(representation):
                        f['has_drm'] = True
                    representation_ms_info = extract_multisegment_info(representation, adaptation_set_ms_info)

                    def prepare_template(template_name, identifiers):
                        tmpl = representation_ms_info[template_name]
                        # First of, % characters outside $...$ templates
                        # must be escaped by doubling for proper processing
                        # by % operator string formatting used further (see
                        # https://github.com/ytdl-org/youtube-dl/issues/16867).
                        t = ''
                        in_template = False
                        for c in tmpl:
                            t += c
                            if c == '$':
                                in_template = not in_template
                            elif c == '%' and not in_template:
                                t += c
                        # Next, $...$ templates are translated to their
                        # %(...) counterparts to be used with % operator
                        t = t.replace('$RepresentationID$', representation_id)
                        t = re.sub(r'\$(%s)\$' % '|'.join(identifiers), r'%(\1)d', t)
                        t = re.sub(r'\$(%s)%%([^$]+)\$' % '|'.join(identifiers), r'%(\1)\2', t)
                        t.replace('$$', '$')
                        return t

                    # @initialization is a regular template like @media one
                    # so it should be handled just the same way (see
                    # https://github.com/ytdl-org/youtube-dl/issues/11605)
                    if 'initialization' in representation_ms_info:
                        initialization_template = prepare_template(
                            'initialization',
                            # As per [1, 5.3.9.4.2, Table 15, page 54] $Number$ and
                            # $Time$ shall not be included for @initialization thus
                            # only $Bandwidth$ remains
                            ('Bandwidth', ))
                        representation_ms_info['initialization_url'] = initialization_template % {
                            'Bandwidth': bandwidth,
                        }

                    def location_key(location):
                        return 'url' if re.match(r'^https?://', location) else 'path'

                    def calc_segment_duration():
                        return float_or_none(
                            representation_ms_info['segment_duration'],
                            representation_ms_info['timescale']) if 'segment_duration' in representation_ms_info else None

                    if 'segment_urls' not in representation_ms_info and 'media' in representation_ms_info:

                        media_template = prepare_template('media', ('Number', 'Bandwidth', 'Time'))
                        media_location_key = location_key(media_template)

                        # As per [1, 5.3.9.4.4, Table 16, page 55] $Number$ and $Time$
                        # can't be used at the same time
                        if '%(Number' in media_template and 's' not in representation_ms_info:
                            segment_duration = None
                            if 'total_number' not in representation_ms_info and 'segment_duration' in representation_ms_info:
                                segment_duration = float_or_none(representation_ms_info['segment_duration'], representation_ms_info['timescale'])
                                representation_ms_info['total_number'] = int(math.ceil(
                                    float_or_none(period_duration, segment_duration, default=0)))
                            representation_ms_info['fragments'] = [{
                                media_location_key: media_template % {
                                    'Number': segment_number,
                                    'Bandwidth': bandwidth,
                                },
                                'duration': segment_duration,
                            } for segment_number in range(
                                representation_ms_info['start_number'],
                                representation_ms_info['total_number'] + representation_ms_info['start_number'])]
                        else:
                            # $Number*$ or $Time$ in media template with S list available
                            # Example $Number*$: http://www.svtplay.se/klipp/9023742/stopptid-om-bjorn-borg
                            # Example $Time$: https://play.arkena.com/embed/avp/v2/player/media/b41dda37-d8e7-4d3f-b1b5-9a9db578bdfe/1/129411
                            representation_ms_info['fragments'] = []
                            segment_time = 0
                            segment_d = None
                            segment_number = representation_ms_info['start_number']

                            def add_segment_url():
                                segment_url = media_template % {
                                    'Time': segment_time,
                                    'Bandwidth': bandwidth,
                                    'Number': segment_number,
                                }
                                representation_ms_info['fragments'].append({
                                    media_location_key: segment_url,
                                    'duration': float_or_none(segment_d, representation_ms_info['timescale']),
                                })

                            for num, s in enumerate(representation_ms_info['s']):
                                segment_time = s.get('t') or segment_time
                                segment_d = s['d']
                                add_segment_url()
                                segment_number += 1
                                for r in range(s.get('r', 0)):
                                    segment_time += segment_d
                                    add_segment_url()
                                    segment_number += 1
                                segment_time += segment_d
                    elif 'segment_urls' in representation_ms_info:
                        fragments = []
                        if 's' in representation_ms_info:
                            # No media template
                            # Example: https://www.youtube.com/watch?v=iXZV5uAYMJI
                            # or any YouTube dashsegments video
                            segment_index = 0
                            timescale = representation_ms_info['timescale']
                            for s in representation_ms_info['s']:
                                duration = float_or_none(s['d'], timescale)
                                for r in range(s.get('r', 0) + 1):
                                    segment_uri = representation_ms_info['segment_urls'][segment_index]
                                    fragments.append({
                                        location_key(segment_uri): segment_uri,
                                        'duration': duration,
                                    })
                                    segment_index += 1
                        elif 'segment_urls_range' in representation_ms_info:
                            # Segment URLs with mediaRange
                            # Example: https://kinescope.io/200615537/master.mpd
                            # https://github.com/ytdl-org/youtube-dl/issues/30235
                            # or any mpd generated with Bento4 `mp4dash --no-split --use-segment-list`
                            segment_duration = calc_segment_duration()
                            for segment_url, segment_url_range in zip(
                                    representation_ms_info['segment_urls'], representation_ms_info['segment_urls_range']):
                                fragments.append({
                                    location_key(segment_url): segment_url,
                                    'range': segment_url_range,
                                    'duration': segment_duration,
                                })
                        else:
                            # Segment URLs with no SegmentTimeline
                            # Example: https://www.seznam.cz/zpravy/clanek/cesko-zasahne-vitr-o-sile-vichrice-muze-byt-i-zivotu-nebezpecny-39091
                            # https://github.com/ytdl-org/youtube-dl/pull/14844
                            segment_duration = calc_segment_duration()
                            for segment_url in representation_ms_info['segment_urls']:
                                fragments.append({
                                    location_key(segment_url): segment_url,
                                    'duration': segment_duration,
                                })
                        representation_ms_info['fragments'] = fragments

                    # If there is a fragments key available then we correctly recognized fragmented media.
                    # Otherwise we will assume unfragmented media with direct access. Technically, such
                    # assumption is not necessarily correct since we may simply have no support for
                    # some forms of fragmented media renditions yet, but for now we'll use this fallback.
                    if 'fragments' in representation_ms_info:
                        base_url = representation_ms_info['base_url']
                        f.update({
                            # NB: mpd_url may be empty when MPD manifest is parsed from a string
                            'url': mpd_url or base_url,
                            'fragment_base_url': base_url,
                            'fragments': [],
                            'protocol': 'http_dash_segments',
                        })
                        if 'initialization_url' in representation_ms_info and 'initialization_url_range' in representation_ms_info:
                            # Initialization URL with range (accompanied by Segment URLs with mediaRange above)
                            # https://github.com/ytdl-org/youtube-dl/issues/30235
                            initialization_url = representation_ms_info['initialization_url']
                            f['fragments'].append({
                                location_key(initialization_url): initialization_url,
                                'range': representation_ms_info['initialization_url_range'],
                            })
                        elif 'initialization_url' in representation_ms_info:
                            initialization_url = representation_ms_info['initialization_url']
                            if not f.get('url'):
                                f['url'] = initialization_url
                            f['fragments'].append({location_key(initialization_url): initialization_url})
                        elif 'initialization_url_range' in representation_ms_info:
                            # no Initialization URL but range (accompanied by no Segment URLs but mediaRange above)
                            # https://github.com/ytdl-org/youtube-dl/issues/27575
                            f['fragments'].append({
                                location_key(base_url): base_url,
                                'range': representation_ms_info['initialization_url_range'],
                            })
                        f['fragments'].extend(representation_ms_info['fragments'])
                        if not period_duration:
                            period_duration = sum(traverse_obj(representation_ms_info, (
                                'fragments', Ellipsis, 'duration', T(float_or_none))))
                    else:
                        # Assuming direct URL to unfragmented media.
                        f['url'] = representation_ms_info['base_url']
                    if content_type in ('video', 'audio', 'image/jpeg'):
                        f['manifest_stream_number'] = stream_numbers[f['url']]
                        stream_numbers[f['url']] += 1
                        formats.append(f)
                    elif content_type == 'text':
                        subtitles.setdefault(lang or 'und', []).append(f)
        return formats, subtitles