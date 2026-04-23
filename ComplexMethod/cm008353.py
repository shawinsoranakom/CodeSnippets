def _real_extract(self, url):
        article_id = self._match_id(url)
        webpage = self._download_webpage(url, article_id)
        bc_url = self._extract_bc_embed_url(webpage)

        if not bc_url:
            fusion_metadata = self._parse_json(
                self._search_regex(r'Fusion\.globalContent\s*=\s*({.+?})\s*;', webpage, 'fusion metadata'), article_id)

            video_metadata = fusion_metadata.get('video')
            if not video_metadata:
                custom_video_id = traverse_obj(fusion_metadata, ('customVideo', 'embed', 'id'), expected_type=str)
                if custom_video_id:
                    video_metadata = self._download_json(
                        'https://www.nzherald.co.nz/pf/api/v3/content/fetch/full-content-by-id', article_id,
                        query={'query': json.dumps({'id': custom_video_id, 'site': 'nzh'}), '_website': 'nzh'})
            bc_video_id = traverse_obj(
                video_metadata or fusion_metadata,  # fusion metadata is the video metadata for video-only pages
                'brightcoveId', ('content_elements', ..., 'referent', 'id'),
                get_all=False, expected_type=str)

            if not bc_video_id:
                if isinstance(video_metadata, dict) and len(video_metadata) == 0:
                    raise ExtractorError('This article does not have a video.', expected=True)
                else:
                    raise ExtractorError('Failed to extract brightcove video id')
            bc_url = self.BRIGHTCOVE_URL_TEMPLATE % bc_video_id

        return self.url_result(bc_url, 'BrightcoveNew')