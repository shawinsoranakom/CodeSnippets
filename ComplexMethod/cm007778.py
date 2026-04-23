def _extract_urls(ie, webpage, video_id):
        entries = []
        for mobj in re.finditer(AnvatoIE._ANVP_RE, webpage):
            anvplayer_data = ie._parse_json(
                mobj.group('anvp'), video_id, transform_source=unescapeHTML,
                fatal=False)
            if not anvplayer_data:
                continue
            video = anvplayer_data.get('video')
            if not isinstance(video, compat_str) or not video.isdigit():
                continue
            access_key = anvplayer_data.get('accessKey')
            if not access_key:
                mcp = anvplayer_data.get('mcp')
                if mcp:
                    access_key = AnvatoIE._MCP_TO_ACCESS_KEY_TABLE.get(
                        mcp.lower())
            if not access_key:
                continue
            entries.append(ie.url_result(
                'anvato:%s:%s' % (access_key, video), ie=AnvatoIE.ie_key(),
                video_id=video))
        return entries