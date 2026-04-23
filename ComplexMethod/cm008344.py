def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        fusion_metadata = self._search_json(r'Fusion\.globalContent\s*=', webpage, 'fusion metadata', display_id)

        entries = []
        for item in traverse_obj(fusion_metadata, 'content_elements') or []:
            item_type = traverse_obj(item, 'subtype')
            if item_type == 'video':
                brightcove_config = traverse_obj(item, ('embed', 'config'))
                brightcove_url = self.BRIGHTCOVE_URL_TEMPLATE % (
                    traverse_obj(brightcove_config, 'brightcoveAccount') or '963482464001',
                    traverse_obj(brightcove_config, 'brightcoveVideoId'),
                )
                entries.append(self.url_result(brightcove_url, BrightcoveNewIE))
            elif item_type == 'youtube':
                video_id_or_url = traverse_obj(item, ('referent', 'id'), ('raw_oembed', '_id'))
                if video_id_or_url:
                    entries.append(self.url_result(video_id_or_url, ie='Youtube'))

        if not entries:
            raise ExtractorError('This article does not have a video.', expected=True)

        playlist_title = (
            traverse_obj(fusion_metadata, ('headlines', 'basic'))
            or self._generic_title('', webpage)
        )
        return self.playlist_result(entries, display_id, playlist_title)