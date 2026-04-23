def _extract_mgid(self, webpage):
        try:
            # the url can be http://media.mtvnservices.com/fb/{mgid}.swf
            # or http://media.mtvnservices.com/{mgid}
            og_url = self._og_search_video_url(webpage)
            mgid = url_basename(og_url)
            if mgid.endswith('.swf'):
                mgid = mgid[:-4]
        except RegexNotFoundError:
            mgid = None

        if mgid is None or ':' not in mgid:
            mgid = self._search_regex(
                [r'data-mgid="(.*?)"', r'swfobject\.embedSWF\(".*?(mgid:.*?)"'],
                webpage, 'mgid', default=None)

        if not mgid:
            sm4_embed = self._html_search_meta(
                'sm4:video:embed', webpage, 'sm4 embed', default='')
            mgid = self._search_regex(
                r'embed/(mgid:.+?)["\'&?/]', sm4_embed, 'mgid', default=None)

        if not mgid:
            mgid = self._extract_triforce_mgid(webpage)

        if not mgid:
            data = self._parse_json(self._search_regex(
                r'__DATA__\s*=\s*({.+?});', webpage, 'data'), None)
            main_container = self._extract_child_with_type(data, 'MainContainer')
            ab_testing = self._extract_child_with_type(main_container, 'ABTesting')
            video_player = self._extract_child_with_type(ab_testing or main_container, 'VideoPlayer')
            mgid = video_player['props']['media']['video']['config']['uri']

        return mgid