def _extract_video(self, video_block):
        video_element = self._search_regex(
            self._VIDEO_ELEMENT_REGEX, video_block, 'video element', default=None)
        if video_element:
            video_element_attrs = extract_attributes(video_element)
            video_id = video_element_attrs.get('data-video-id')
            if not video_id:
                return
            account_id = video_element_attrs.get('data-account') or '876450610001'
            player_id = video_element_attrs.get('adjustplayer') or '19dszYXgm'
        else:
            video_block_attrs = extract_attributes(video_block)
            video_id = video_block_attrs.get('videoid')
            if not video_id:
                return
            account_id = video_block_attrs.get('accountid') or '876630703001'
            player_id = video_block_attrs.get('playerid') or 'KbPwEbuHx'
        return self.url_result(
            self.BRIGHTCOVE_URL_TEMPLATE % (account_id, player_id, video_id),
            'BrightcoveNew', video_id)