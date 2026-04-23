def _parse_ism_formats(self, ism_doc, ism_url, ism_id=None):
        """
        Parse formats from ISM manifest.
        References:
         1. [MS-SSTR]: Smooth Streaming Protocol,
            https://msdn.microsoft.com/en-us/library/ff469518.aspx
        """
        if ism_doc.get('IsLive') == 'TRUE' or ism_doc.find('Protection') is not None:
            return []

        duration = int(ism_doc.attrib['Duration'])
        timescale = int_or_none(ism_doc.get('TimeScale')) or 10000000

        formats = []
        for stream in ism_doc.findall('StreamIndex'):
            stream_type = stream.get('Type')
            if stream_type not in ('video', 'audio'):
                continue
            url_pattern = stream.attrib['Url']
            stream_timescale = int_or_none(stream.get('TimeScale')) or timescale
            stream_name = stream.get('Name')
            for track in stream.findall('QualityLevel'):
                fourcc = track.get('FourCC', 'AACL' if track.get('AudioTag') == '255' else None)
                # TODO: add support for WVC1 and WMAP
                if fourcc not in ('H264', 'AVC1', 'AACL'):
                    self.report_warning('%s is not a supported codec' % fourcc)
                    continue
                tbr = int(track.attrib['Bitrate']) // 1000
                # [1] does not mention Width and Height attributes. However,
                # they're often present while MaxWidth and MaxHeight are
                # missing, so should be used as fallbacks
                width = int_or_none(track.get('MaxWidth') or track.get('Width'))
                height = int_or_none(track.get('MaxHeight') or track.get('Height'))
                sampling_rate = int_or_none(track.get('SamplingRate'))

                track_url_pattern = re.sub(r'{[Bb]itrate}', track.attrib['Bitrate'], url_pattern)
                track_url_pattern = compat_urlparse.urljoin(ism_url, track_url_pattern)

                fragments = []
                fragment_ctx = {
                    'time': 0,
                }
                stream_fragments = stream.findall('c')
                for stream_fragment_index, stream_fragment in enumerate(stream_fragments):
                    fragment_ctx['time'] = int_or_none(stream_fragment.get('t')) or fragment_ctx['time']
                    fragment_repeat = int_or_none(stream_fragment.get('r')) or 1
                    fragment_ctx['duration'] = int_or_none(stream_fragment.get('d'))
                    if not fragment_ctx['duration']:
                        try:
                            next_fragment_time = int(stream_fragment[stream_fragment_index + 1].attrib['t'])
                        except IndexError:
                            next_fragment_time = duration
                        fragment_ctx['duration'] = (next_fragment_time - fragment_ctx['time']) / fragment_repeat
                    for _ in range(fragment_repeat):
                        fragments.append({
                            'url': re.sub(r'{start[ _]time}', compat_str(fragment_ctx['time']), track_url_pattern),
                            'duration': fragment_ctx['duration'] / stream_timescale,
                        })
                        fragment_ctx['time'] += fragment_ctx['duration']

                format_id = []
                if ism_id:
                    format_id.append(ism_id)
                if stream_name:
                    format_id.append(stream_name)
                format_id.append(compat_str(tbr))

                formats.append({
                    'format_id': '-'.join(format_id),
                    'url': ism_url,
                    'manifest_url': ism_url,
                    'ext': 'ismv' if stream_type == 'video' else 'isma',
                    'width': width,
                    'height': height,
                    'tbr': tbr,
                    'asr': sampling_rate,
                    'vcodec': 'none' if stream_type == 'audio' else fourcc,
                    'acodec': 'none' if stream_type == 'video' else fourcc,
                    'protocol': 'ism',
                    'fragments': fragments,
                    '_download_params': {
                        'duration': duration,
                        'timescale': stream_timescale,
                        'width': width or 0,
                        'height': height or 0,
                        'fourcc': fourcc,
                        'codec_private_data': track.get('CodecPrivateData'),
                        'sampling_rate': sampling_rate,
                        'channels': int_or_none(track.get('Channels', 2)),
                        'bits_per_sample': int_or_none(track.get('BitsPerSample', 16)),
                        'nal_unit_length_field': int_or_none(track.get('NALUnitLengthField', 4)),
                    },
                })
        return formats