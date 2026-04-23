def _build_selector_function(selector):
            if isinstance(selector, list):
                fs = [_build_selector_function(s) for s in selector]

                def selector_function(ctx):
                    for f in fs:
                        for format in f(ctx):
                            yield format
                return selector_function
            elif selector.type == GROUP:
                selector_function = _build_selector_function(selector.selector)
            elif selector.type == PICKFIRST:
                fs = [_build_selector_function(s) for s in selector.selector]

                def selector_function(ctx):
                    for f in fs:
                        picked_formats = list(f(ctx))
                        if picked_formats:
                            return picked_formats
                    return []
            elif selector.type == SINGLE:
                format_spec = selector.selector

                def selector_function(ctx):
                    formats = list(ctx['formats'])
                    if not formats:
                        return
                    if format_spec == 'all':
                        for f in formats:
                            yield f
                    elif format_spec in ['best', 'worst', None]:
                        format_idx = 0 if format_spec == 'worst' else -1
                        audiovideo_formats = [
                            f for f in formats
                            if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                        if audiovideo_formats:
                            yield audiovideo_formats[format_idx]
                        # for extractors with incomplete formats (audio only (soundcloud)
                        # or video only (imgur)) we will fallback to best/worst
                        # {video,audio}-only format
                        elif ctx['incomplete_formats']:
                            yield formats[format_idx]
                    elif format_spec == 'bestaudio':
                        audio_formats = [
                            f for f in formats
                            if f.get('vcodec') == 'none']
                        if audio_formats:
                            yield audio_formats[-1]
                    elif format_spec == 'worstaudio':
                        audio_formats = [
                            f for f in formats
                            if f.get('vcodec') == 'none']
                        if audio_formats:
                            yield audio_formats[0]
                    elif format_spec == 'bestvideo':
                        video_formats = [
                            f for f in formats
                            if f.get('acodec') == 'none']
                        if video_formats:
                            yield video_formats[-1]
                    elif format_spec == 'worstvideo':
                        video_formats = [
                            f for f in formats
                            if f.get('acodec') == 'none']
                        if video_formats:
                            yield video_formats[0]
                    else:
                        extensions = ['mp4', 'flv', 'webm', '3gp', 'm4a', 'mp3', 'ogg', 'aac', 'wav']
                        if format_spec in extensions:
                            filter_f = lambda f: f['ext'] == format_spec
                        else:
                            filter_f = lambda f: f['format_id'] == format_spec
                        matches = list(filter(filter_f, formats))
                        if matches:
                            yield matches[-1]
            elif selector.type == MERGE:
                def _merge(formats_info):
                    format_1, format_2 = [f['format_id'] for f in formats_info]
                    # The first format must contain the video and the
                    # second the audio
                    if formats_info[0].get('vcodec') == 'none':
                        self.report_error('The first format must '
                                          'contain the video, try using '
                                          '"-f %s+%s"' % (format_2, format_1))
                        return
                    # Formats must be opposite (video+audio)
                    if formats_info[0].get('acodec') == 'none' and formats_info[1].get('acodec') == 'none':
                        self.report_error(
                            'Both formats %s and %s are video-only, you must specify "-f video+audio"'
                            % (format_1, format_2))
                        return
                    output_ext = (
                        formats_info[0]['ext']
                        if self.params.get('merge_output_format') is None
                        else self.params['merge_output_format'])
                    return {
                        'requested_formats': formats_info,
                        'format': '%s+%s' % (formats_info[0].get('format'),
                                             formats_info[1].get('format')),
                        'format_id': '%s+%s' % (formats_info[0].get('format_id'),
                                                formats_info[1].get('format_id')),
                        'width': formats_info[0].get('width'),
                        'height': formats_info[0].get('height'),
                        'resolution': formats_info[0].get('resolution'),
                        'fps': formats_info[0].get('fps'),
                        'vcodec': formats_info[0].get('vcodec'),
                        'vbr': formats_info[0].get('vbr'),
                        'stretched_ratio': formats_info[0].get('stretched_ratio'),
                        'acodec': formats_info[1].get('acodec'),
                        'abr': formats_info[1].get('abr'),
                        'ext': output_ext,
                    }

                def selector_function(ctx):
                    selector_fn = lambda x: _build_selector_function(x)(ctx)
                    for pair in itertools.product(*map(selector_fn, selector.selector)):
                        yield _merge(pair)

            filters = [self._build_format_filter(f) for f in selector.filters]

            def final_selector(ctx):
                ctx_copy = dict(ctx)
                for _filter in filters:
                    ctx_copy['formats'] = list(filter(_filter, ctx_copy['formats']))
                return selector_function(ctx_copy)
            return final_selector