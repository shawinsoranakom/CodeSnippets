def _search_json_ld(self, html, video_id, expected_type=None, **kwargs):
        json_ld_list = list(re.finditer(JSON_LD_RE, html))
        default = kwargs.get('default', NO_DEFAULT)
        # JSON-LD may be malformed and thus `fatal` should be respected.
        # At the same time `default` may be passed that assumes `fatal=False`
        # for _search_regex. Let's simulate the same behavior here as well.
        fatal = kwargs.get('fatal', True) if default == NO_DEFAULT else False
        json_ld = []
        for mobj in json_ld_list:
            json_ld_item = self._parse_json(
                mobj.group('json_ld'), video_id, fatal=fatal)
            if not json_ld_item:
                continue
            if isinstance(json_ld_item, dict):
                json_ld.append(json_ld_item)
            elif isinstance(json_ld_item, (list, tuple)):
                json_ld.extend(json_ld_item)
        if json_ld:
            json_ld = self._json_ld(json_ld, video_id, fatal=fatal, expected_type=expected_type)
        if json_ld:
            return json_ld
        if default is not NO_DEFAULT:
            return default
        elif fatal:
            raise RegexNotFoundError('Unable to extract JSON-LD')
        else:
            self.report_warning('unable to extract JSON-LD %s' % bug_reports_message())
            return {}