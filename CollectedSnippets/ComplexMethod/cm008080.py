def _real_extract(self, url):
        canonical_id = self._match_id(url)
        # Make sure to get the correct ID in case of redirects
        urlh = self._request_webpage(url, canonical_id)
        canonical_id = self._search_regex(self._VALID_URL, urlh.url, 'channel id', group='id')
        season_number = traverse_obj(parse_qs(url), ('staffel', -1, {int_or_none}))
        playlist_id = join_nonempty(canonical_id, season_number and f's{season_number}')

        collection_data = self._download_graphql(
            playlist_id, 'smart collection data', query={
                'operationName': 'GetSmartCollectionByCanonical',
                'variables': json.dumps({
                    'canonical': canonical_id,
                    'videoPageSize': 100,  # Use max page size to get episodes from all seasons
                }),
                'extensions': json.dumps({
                    'persistedQuery': {
                        'version': 1,
                        'sha256Hash': 'cb49420e133bd668ad895a8cea0e65cba6aa11ac1cacb02341ff5cf32a17cd02',
                    },
                }),
            })['data']['smartCollectionByCanonical']
        video_data = traverse_obj(collection_data, ('video', {dict})) or {}
        season_numbers = traverse_obj(collection_data, ('seasons', 'seasons', ..., 'number', {int_or_none}))

        if not self._yes_playlist(
            season_numbers and playlist_id,
            url_or_none(video_data.get('sharingUrl')) and video_data.get('canonical'),
        ):
            return self.url_result(video_data['sharingUrl'], ZDFIE, video_data['canonical'])

        if season_number is not None and season_number not in season_numbers:
            raise ExtractorError(f'Season {season_number} was not found in the collection data')

        return self.playlist_result(
            self._entries(playlist_id, canonical_id, season_numbers, season_number),
            playlist_id, join_nonempty(
                traverse_obj(collection_data, ('title', {str})),
                season_number and f'Season {season_number}', delim=' - '),
            traverse_obj(collection_data, ('infoText', {str})))