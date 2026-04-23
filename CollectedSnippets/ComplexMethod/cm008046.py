def _build_selector_function(selector):
            if isinstance(selector, list):  # ,
                fs = [_build_selector_function(s) for s in selector]

                def selector_function(ctx):
                    for f in fs:
                        yield from f(ctx)
                return selector_function

            elif selector.type == GROUP:  # ()
                selector_function = _build_selector_function(selector.selector)

            elif selector.type == PICKFIRST:  # /
                fs = [_build_selector_function(s) for s in selector.selector]

                def selector_function(ctx):
                    for f in fs:
                        picked_formats = list(f(ctx))
                        if picked_formats:
                            return picked_formats
                    return []

            elif selector.type == MERGE:  # +
                selector_1, selector_2 = map(_build_selector_function, selector.selector)

                def selector_function(ctx):
                    for pair in itertools.product(selector_1(ctx), selector_2(ctx)):
                        yield _merge(pair)

            elif selector.type == SINGLE:  # atom
                format_spec = selector.selector or 'best'

                # TODO: Add allvideo, allaudio etc by generalizing the code with best/worst selector
                if format_spec == 'all':
                    def selector_function(ctx):
                        yield from _check_formats(ctx['formats'][::-1])
                elif format_spec == 'mergeall':
                    def selector_function(ctx):
                        formats = list(_check_formats(
                            f for f in ctx['formats'] if f.get('vcodec') != 'none' or f.get('acodec') != 'none'))
                        if not formats:
                            return
                        merged_format = formats[-1]
                        for f in formats[-2::-1]:
                            merged_format = _merge((merged_format, f))
                        yield merged_format

                else:
                    format_fallback, seperate_fallback, format_reverse, format_idx = False, None, True, 1
                    mobj = re.match(
                        r'(?P<bw>best|worst|b|w)(?P<type>video|audio|v|a)?(?P<mod>\*)?(?:\.(?P<n>[1-9]\d*))?$',
                        format_spec)
                    if mobj is not None:
                        format_idx = int_or_none(mobj.group('n'), default=1)
                        format_reverse = mobj.group('bw')[0] == 'b'
                        format_type = (mobj.group('type') or [None])[0]
                        not_format_type = {'v': 'a', 'a': 'v'}.get(format_type)
                        format_modified = mobj.group('mod') is not None

                        format_fallback = not format_type and not format_modified  # for b, w
                        _filter_f = (
                            (lambda f: f.get(f'{format_type}codec') != 'none')
                            if format_type and format_modified  # bv*, ba*, wv*, wa*
                            else (lambda f: f.get(f'{not_format_type}codec') == 'none')
                            if format_type  # bv, ba, wv, wa
                            else (lambda f: f.get('vcodec') != 'none' and f.get('acodec') != 'none')
                            if not format_modified  # b, w
                            else lambda f: True)  # b*, w*
                        filter_f = lambda f: _filter_f(f) and (
                            f.get('vcodec') != 'none' or f.get('acodec') != 'none')
                    else:
                        if format_spec in self._format_selection_exts['audio']:
                            filter_f = lambda f: f.get('ext') == format_spec and f.get('acodec') != 'none'
                        elif format_spec in self._format_selection_exts['video']:
                            filter_f = lambda f: f.get('ext') == format_spec and f.get('acodec') != 'none' and f.get('vcodec') != 'none'
                            seperate_fallback = lambda f: f.get('ext') == format_spec and f.get('vcodec') != 'none'
                        elif format_spec in self._format_selection_exts['storyboards']:
                            filter_f = lambda f: f.get('ext') == format_spec and f.get('acodec') == 'none' and f.get('vcodec') == 'none'
                        else:
                            filter_f = lambda f: f.get('format_id') == format_spec  # id

                    def selector_function(ctx):
                        formats = list(ctx['formats'])
                        matches = list(filter(filter_f, formats)) if filter_f is not None else formats
                        if not matches:
                            if format_fallback and ctx['incomplete_formats']:
                                # for extractors with incomplete formats (audio only (soundcloud)
                                # or video only (imgur)) best/worst will fallback to
                                # best/worst {video,audio}-only format
                                matches = list(filter(lambda f: f.get('vcodec') != 'none' or f.get('acodec') != 'none', formats))
                            elif seperate_fallback and not ctx['has_merged_format']:
                                # for compatibility with youtube-dl when there is no pre-merged format
                                matches = list(filter(seperate_fallback, formats))
                        matches = LazyList(_check_formats(matches[::-1 if format_reverse else 1]))
                        try:
                            yield matches[format_idx - 1]
                        except LazyList.IndexError:
                            return

            filters = [self._build_format_filter(f) for f in selector.filters]

            def final_selector(ctx):
                ctx_copy = dict(ctx)
                for _filter in filters:
                    ctx_copy['formats'] = list(filter(_filter, ctx_copy['formats']))
                return selector_function(ctx_copy)
            return final_selector