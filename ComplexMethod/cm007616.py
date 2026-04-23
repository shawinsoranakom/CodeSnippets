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