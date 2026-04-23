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
            object_doc = compat_etree_fromstring(object_str.encode('utf-8'))
        except compat_xml_parse_error:
            return

        fv_el = find_xpath_attr(object_doc, './param', 'name', 'flashVars')
        if fv_el is not None:
            flashvars = dict(
                (k, v[0])
                for k, v in compat_parse_qs(fv_el.attrib['value']).items())
        else:
            flashvars = {}

        data_url = object_doc.attrib.get('data', '')
        data_url_params = compat_parse_qs(compat_urllib_parse_urlparse(data_url).query)

        def find_param(name):
            if name in flashvars:
                return flashvars[name]
            node = find_xpath_attr(object_doc, './param', 'name', name)
            if node is not None:
                return node.attrib['value']
            return data_url_params.get(name)

        params = {}

        playerID = find_param('playerID') or find_param('playerId')
        if playerID is None:
            raise ExtractorError('Cannot find player ID')
        params['playerID'] = playerID

        playerKey = find_param('playerKey')
        # Not all pages define this value
        if playerKey is not None:
            params['playerKey'] = playerKey
        # These fields hold the id of the video
        videoPlayer = find_param('@videoPlayer') or find_param('videoId') or find_param('videoID') or find_param('@videoList')
        if videoPlayer is not None:
            if isinstance(videoPlayer, list):
                videoPlayer = videoPlayer[0]
            videoPlayer = videoPlayer.strip()
            # UUID is also possible for videoPlayer (e.g.
            # http://www.popcornflix.com/hoodies-vs-hooligans/7f2d2b87-bbf2-4623-acfb-ea942b4f01dd
            # or http://www8.hp.com/cn/zh/home.html)
            if not (re.match(
                    r'^(?:\d+|[\da-fA-F]{8}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{4}-?[\da-fA-F]{12})$',
                    videoPlayer) or videoPlayer.startswith('ref:')):
                return None
            params['@videoPlayer'] = videoPlayer
        linkBase = find_param('linkBaseURL')
        if linkBase is not None:
            params['linkBaseURL'] = linkBase
        return cls._make_brightcove_url(params)