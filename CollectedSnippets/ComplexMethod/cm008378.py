def _yield_json_ld(self, html, video_id, *, fatal=True, default=NO_DEFAULT):
        """Yield all json ld objects in the html"""
        if default is not NO_DEFAULT:
            fatal = False
        if not fatal and not isinstance(html, str):
            return
        for mobj in re.finditer(JSON_LD_RE, html):
            json_ld_item = self._parse_json(
                mobj.group('json_ld'), video_id, fatal=fatal,
                errnote=False if default is not NO_DEFAULT else None)
            for json_ld in variadic(json_ld_item):
                if isinstance(json_ld, dict):
                    yield json_ld