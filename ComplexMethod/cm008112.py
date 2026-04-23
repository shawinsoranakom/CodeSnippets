def _real_extract(self, url):
        locale, slug = self._match_valid_url(url).group('locale', 'slug')

        language, _, country = (locale or 'US').rpartition('-')
        parsed_locale = f'{language.lower() or "en"}_{country.upper()}'
        self.write_debug(f'Using locale {parsed_locale} (from {locale})', only_once=True)

        response = self._download_json('https://graph.nintendo.com/', slug, query={
            'operationName': 'NintendoDirect',
            'variables': json.dumps({
                'locale': parsed_locale,
                'slug': slug,
            }, separators=(',', ':')),
            'extensions': json.dumps({
                'persistedQuery': {
                    'version': 1,
                    'sha256Hash': '969b16fe9f08b686fa37bc44d1fd913b6188e65794bb5e341c54fa683a8004cb',
                },
            }, separators=(',', ':')),
        })
        # API returns `{"data": {"direct": null}}` if no matching id
        direct_info = traverse_obj(response, ('data', 'direct', {dict}))
        if not direct_info:
            raise ExtractorError(f'No Nintendo Direct with id {slug} exists', expected=True)

        errors = ', '.join(traverse_obj(response, ('errors', ..., 'message')))
        if errors:
            raise ExtractorError(f'GraphQL API error: {errors or "Unknown error"}')

        result = traverse_obj(direct_info, {
            'id': ('id', {str}),
            'title': ('name', {str}),
            'timestamp': ('startDate', {unified_timestamp}),
            'description': ('description', 'text', {str}),
            'age_limit': ('contentRating', 'order', {int}),
            'tags': ('contentDescriptors', ..., 'label', {str}),
            'thumbnail': ('thumbnail', {self._create_asset_url}),
        })
        result['display_id'] = slug

        asset_id = traverse_obj(direct_info, ('video', 'publicId', {str}))
        if not asset_id:
            youtube_id = traverse_obj(direct_info, ('liveStream', {str}))
            if not youtube_id:
                self.raise_no_formats('Could not find any video formats', video_id=slug)

            return self.url_result(youtube_id, **result, url_transparent=True)

        if asset_id.startswith('Legacy Videos/'):
            result['_old_archive_ids'] = [make_archive_id(self, asset_id[14:])]
        result['formats'] = self._extract_m3u8_formats(
            self._create_asset_url(f'/video/upload/sp_full_hd/v1/{asset_id}.m3u8'), slug)

        return result