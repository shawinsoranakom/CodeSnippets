def _extract_embed_urls(cls, url, webpage):
        # https://docs.glomex.com/publisher/video-player-integration/javascript-api/
        quot_re = r'["\']'

        regex = fr'''(?x)
            <iframe[^>]+?src=(?P<q>{quot_re})(?P<url>
                (?:https?:)?{cls._BASE_PLAYER_URL_RE}\?(?:(?!(?P=q)).)+
            )(?P=q)'''
        for mobj in re.finditer(regex, webpage):
            embed_url = unescapeHTML(mobj.group('url'))
            if cls.suitable(embed_url):
                yield cls._smuggle_origin_url(embed_url, url)

        regex = fr'''(?x)
            <glomex-player [^>]+?>|
            <div[^>]* data-glomex-player=(?P<q>{quot_re})true(?P=q)[^>]*>'''
        for mobj in re.finditer(regex, webpage):
            attrs = extract_attributes(mobj.group(0))
            if attrs.get('data-integration-id') and attrs.get('data-playlist-id'):
                yield cls.build_player_url(attrs['data-playlist-id'], attrs['data-integration-id'], url)

        # naive parsing of inline scripts for hard-coded integration parameters
        regex = fr'''(?x)
            (?P<is_js>dataset\.)?%s\s*(?(is_js)=|:)\s*
            (?P<q>{quot_re})(?P<id>(?:(?!(?P=q)).)+)(?P=q)\s'''
        for mobj in re.finditer(r'(?x)<script[^<]*>.+?</script>', webpage):
            script = mobj.group(0)
            integration_id = re.search(regex % 'integrationId', script)
            if not integration_id:
                continue
            playlist_id = re.search(regex % 'playlistId', script)
            if playlist_id:
                yield cls.build_player_url(playlist_id, integration_id, url)