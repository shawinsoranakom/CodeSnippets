def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        # Change the 'videoId' and others field to '@videoPlayer'
        url = re.sub(r'(?<=[?&])(videoI(d|D)|idVideo|bctid)', '%40videoPlayer', url)
        # Change bckey (used by bcove.me urls) to playerKey
        url = re.sub(r'(?<=[?&])bckey', 'playerKey', url)
        mobj = self._match_valid_url(url)
        query_str = mobj.group('query')
        query = urllib.parse.parse_qs(query_str)

        video_player = query.get('@videoPlayer')
        if video_player:
            # We set the original url as the default 'Referer' header
            referer = query.get('linkBaseURL', [None])[0] or smuggled_data.get('Referer', url)
            video_id = video_player[0]
            if 'playerID' not in query:
                mobj = re.search(r'/bcpid(\d+)', url)
                if mobj is not None:
                    query['playerID'] = [mobj.group(1)]
            publisher_id = query.get('publisherId')
            if publisher_id and publisher_id[0].isdigit():
                publisher_id = publisher_id[0]
            if not publisher_id:
                player_key = query.get('playerKey')
                if player_key and ',' in player_key[0]:
                    player_key = player_key[0]
                else:
                    player_id = query.get('playerID')
                    if player_id and player_id[0].isdigit():
                        headers = {}
                        if referer:
                            headers['Referer'] = referer
                        player_page = self._download_webpage(
                            'https://link.brightcove.com/services/player/bcpid' + player_id[0],
                            video_id, headers=headers, fatal=False)
                        if player_page:
                            player_key = self._search_regex(
                                r'<param\s+name="playerKey"\s+value="([\w~,-]+)"',
                                player_page, 'player key', fatal=False)
                if player_key:
                    enc_pub_id = player_key.split(',')[1].replace('~', '=')
                    publisher_id = struct.unpack('>Q', base64.urlsafe_b64decode(enc_pub_id))[0]
            if publisher_id:
                brightcove_new_url = f'https://players.brightcove.net/{publisher_id}/default_default/index.html?videoId={video_id}'
                if referer:
                    brightcove_new_url = smuggle_url(brightcove_new_url, {'referrer': referer})
                return self.url_result(brightcove_new_url, BrightcoveNewIE.ie_key(), video_id)
        # TODO: figure out if it's possible to extract playlistId from playerKey
        # elif 'playerKey' in query:
        #     player_key = query['playerKey']
        #     return self._get_playlist_info(player_key[0])
        raise UnsupportedError(url)