def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)

        page_title = self._og_search_title(webpage, default=None)

        # <video data-brightcove-video-id="5320421710001" data-account="245991542" data-player="SJWAiyYWg" data-embed="default" class="video-js" controls itemscope itemtype="http://schema.org/VideoObject">
        entries = []
        for video in re.findall(r'(?i)(<video[^>]+>)', webpage):
            attrs = extract_attributes(video)

            video_id = attrs.get('data-brightcove-video-id')
            account_id = attrs.get('data-account')
            player_id = attrs.get('data-player')
            embed = attrs.get('data-embed')

            if video_id and account_id and player_id and embed:
                entries.append(
                    f'http://players.brightcove.net/{account_id}/{player_id}_{embed}/index.html?videoId={video_id}')

        if len(entries) == 0:
            return self.url_result(url, 'Generic')
        elif len(entries) == 1:
            return self.url_result(entries[0], 'BrightcoveNew')
        else:
            return self.playlist_from_matches(entries, page_id, page_title, ie='BrightcoveNew')