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