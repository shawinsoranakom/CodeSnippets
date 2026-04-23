def _extract_url_result(self, post):
        if post['type'] == 'video':
            for media in post['media']:
                if media['type'] == 'video':
                    video_id = media['content']
                    source = media['source']
                    if source == 'brightcove':
                        player_code = self._download_webpage(
                            f'http://www.nowness.com/iframe?id={video_id}', video_id,
                            note='Downloading player JavaScript',
                            errnote='Unable to download player JavaScript')
                        bc_url = BrightcoveLegacyIE._extract_brightcove_url(player_code)
                        if bc_url:
                            return self.url_result(bc_url, BrightcoveLegacyIE.ie_key())
                        bc_url = BrightcoveNewIE._extract_url(self, player_code)
                        if bc_url:
                            return self.url_result(bc_url, BrightcoveNewIE.ie_key())
                        raise ExtractorError('Could not find player definition')
                    elif source == 'vimeo':
                        return self.url_result(f'http://vimeo.com/{video_id}', 'Vimeo')
                    elif source == 'youtube':
                        return self.url_result(video_id, 'Youtube')
                    elif source == 'cinematique':
                        # yt-dlp currently doesn't support cinematique
                        # return self.url_result('http://cinematique.com/embed/%s' % video_id, 'Cinematique')
                        pass