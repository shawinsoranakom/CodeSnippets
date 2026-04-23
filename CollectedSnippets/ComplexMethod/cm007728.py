def _get_media_data(self, bu, media_type, media_id):
        query = {'onlyChapters': True} if media_type == 'video' else {}
        full_media_data = self._download_json(
            'https://il.srgssr.ch/integrationlayer/2.0/%s/mediaComposition/%s/%s.json'
            % (bu, media_type, media_id),
            media_id, query=query)['chapterList']
        try:
            media_data = next(
                x for x in full_media_data if x.get('id') == media_id)
        except StopIteration:
            raise ExtractorError('No media information found')

        block_reason = media_data.get('blockReason')
        if block_reason and block_reason in self._ERRORS:
            message = self._ERRORS[block_reason]
            if block_reason == 'GEOBLOCK':
                self.raise_geo_restricted(
                    msg=message, countries=self._GEO_COUNTRIES)
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, message), expected=True)

        return media_data