def _extract_from_webpage(cls, url, webpage):
        for mobj in re.finditer(cls._ANVP_RE, webpage):
            anvplayer_data = unescapeHTML(json.loads(mobj.group('anvp'))) or {}
            video_id, access_key = anvplayer_data.get('video'), anvplayer_data.get('accessKey')
            if not access_key:
                access_key = cls._MCP_TO_ACCESS_KEY_TABLE.get((anvplayer_data.get('mcp') or '').lower())
            if not (video_id or '').isdigit() or not access_key:
                continue
            url = f'anvato:{access_key}:{video_id}'
            if anvplayer_data.get('token'):
                url = smuggle_url(url, {'token': anvplayer_data['token']})
            yield cls.url_result(url, AnvatoIE, video_id)