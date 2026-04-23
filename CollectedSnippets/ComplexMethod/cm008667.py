def _build_brightcove_url(cls, object_str):
        """
        Build a Brightcove url from a xml string containing
        <object class="BrightcoveExperience">{params}</object>
        """

        # Fix up some stupid HTML, see https://github.com/ytdl-org/youtube-dl/issues/1553
        object_str = re.sub(r'(<param(?:\s+[a-zA-Z0-9_]+="[^"]*")*)>',
                            lambda m: m.group(1) + '/>', object_str)
        # Fix up some stupid XML, see https://github.com/ytdl-org/youtube-dl/issues/1608
        object_str = object_str.replace('<--', '<!--')
        # remove namespace to simplify extraction
        object_str = re.sub(r'(<object[^>]*)(xmlns=".*?")', r'\1', object_str)
        object_str = fix_xml_ampersands(object_str)

        try:
            object_doc = compat_etree_fromstring(object_str.encode())
        except xml.etree.ElementTree.ParseError:
            return

        fv_el = find_xpath_attr(object_doc, './param', 'name', 'flashVars')
        if fv_el is not None:
            flashvars = dict(
                (k, v[0])
                for k, v in urllib.parse.parse_qs(fv_el.attrib['value']).items())
        else:
            flashvars = {}

        data_url = object_doc.attrib.get('data', '')
        data_url_params = parse_qs(data_url)

        def find_param(name):
            if name in flashvars:
                return flashvars[name]
            node = find_xpath_attr(object_doc, './param', 'name', name)
            if node is not None:
                return node.attrib['value']
            return data_url_params.get(name)

        params = {}

        player_id = find_param('playerID') or find_param('playerId')
        if player_id is None:
            raise ExtractorError('Cannot find player ID')
        params['playerID'] = player_id

        player_key = find_param('playerKey')
        # Not all pages define this value
        if player_key is not None:
            params['playerKey'] = player_key
        # These fields hold the id of the video
        video_player = find_param('@videoPlayer') or find_param('videoId') or find_param('videoID') or find_param('@videoList')
        if video_player is not None:
            if isinstance(video_player, list):
                video_player = video_player[0]
            video_player = video_player.strip()
            # UUID is also possible for videoPlayer (e.g.
            # http://www.popcornflix.com/hoodies-vs-hooligans/7f2d2b87-bbf2-4623-acfb-ea942b4f01dd
            # or http://www8.hp.com/cn/zh/home.html)
            if not (re.match(
                    r'^(?:\d+|[\da-fA-F]{8}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{12})$',
                    video_player) or video_player.startswith('ref:')):
                return None
            params['@videoPlayer'] = video_player
        link_base = find_param('linkBaseURL')
        if link_base is not None:
            params['linkBaseURL'] = link_base
        return cls._make_brightcove_url(params)