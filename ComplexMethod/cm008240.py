def _real_extract(self, url):
        display_id, url_type = self._match_valid_url(url).group('id', 'url_type')

        qs = parse_qs(url)
        revision_id = traverse_obj(qs, (('revId', 'id'), 0, any))
        if url_type == 'revision':
            revision_id = display_id

        revision_data = None
        if not revision_id:
            post_data = self._call_api(
                'posts', display_id, note='Downloading post data',
                query=traverse_obj(qs, {'sharedKey': ('sharedKey', 0)}))

            revision_id = traverse_obj(post_data, (('revisionId', ('revision', 'id')), {str}, any))
            revision_data = traverse_obj(post_data, ('revision', {dict}))

            if not revision_data and not revision_id:
                post_type = post_data.get('type')
                if post_type == 'Video':
                    return self._parse_video(post_data, url=url)
                if post_type == 'Track':
                    return self._parse_track(post_data, url=url)
                raise ExtractorError(f'Could not extract data for post type {post_type!r}')

        if not revision_data:
            revision_data = self._call_api(
                'revisions', revision_id, note='Downloading revision data', query={'edit': 'false'})

        return self._parse_revision(revision_data, url=url)