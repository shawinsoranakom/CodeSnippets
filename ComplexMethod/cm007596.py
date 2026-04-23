def _search_json(self, start_pattern, string, name, video_id, **kwargs):
        """Searches string for the JSON object specified by start_pattern"""

        # self, start_pattern, string, name, video_id, *, end_pattern='',
        # contains_pattern=r'{(?s:.+)}', fatal=True, default=NO_DEFAULT
        # NB: end_pattern is only used to reduce the size of the initial match
        end_pattern = kwargs.pop('end_pattern', '')
        # (?:[\s\S]) simulates (?(s):.) (eg)
        contains_pattern = kwargs.pop('contains_pattern', r'{[\s\S]+}')
        fatal = kwargs.pop('fatal', True)
        default = kwargs.pop('default', NO_DEFAULT)

        if default is NO_DEFAULT:
            default, has_default = {}, False
        else:
            fatal, has_default = False, True

        json_string = self._search_regex(
            r'(?:{0})\s*(?P<json>{1})\s*(?:{2})'.format(
                start_pattern, contains_pattern, end_pattern),
            string, name, group='json', fatal=fatal, default=None if has_default else NO_DEFAULT)
        if not json_string:
            return default

        # yt-dlp has a special JSON parser that allows trailing text.
        # Until that arrives here, the diagnostic from the exception
        # raised by json.loads() is used to extract the wanted text.
        # Either way, it's a problem if a transform_source() can't
        # handle the trailing text.

        # force an exception
        kwargs['fatal'] = True

        # self._downloader._format_err(name, self._downloader.Styles.EMPHASIS)
        for _ in range(2):
            try:
                # return self._parse_json(json_string, video_id, ignore_extra=True, **kwargs)
                transform_source = kwargs.pop('transform_source', None)
                if transform_source:
                    json_string = transform_source(json_string)
                return self._parse_json(json_string, video_id, **compat_kwargs(kwargs))
            except ExtractorError as e:
                end = int_or_none(self._search_regex(r'\(char\s+(\d+)', error_to_compat_str(e), 'end', default=None))
                if end is not None:
                    json_string = json_string[:end]
                    continue
                msg = 'Unable to extract {0} - Failed to parse JSON'.format(name)
                if fatal:
                    raise ExtractorError(msg, cause=e.cause, video_id=video_id)
                elif not has_default:
                    self.report_warning(
                        '{0}: {1}'.format(msg, error_to_compat_str(e)), video_id=video_id)
            return default