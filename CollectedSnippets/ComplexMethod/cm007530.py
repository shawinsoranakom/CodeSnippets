def _real_extract(self, url):
        video_id = self._match_id(url)
        player_params = self._download_json(
            'http://www.sbs.com.au/api/video_pdkvars/id/%s?form=json' % video_id, video_id)

        error = player_params.get('error')
        if error:
            error_message = 'Sorry, The video you are looking for does not exist.'
            video_data = error.get('results') or {}
            error_code = error.get('errorCode')
            if error_code == 'ComingSoon':
                error_message = '%s is not yet available.' % video_data.get('title', '')
            elif error_code in ('Forbidden', 'intranetAccessOnly'):
                error_message = 'Sorry, This video cannot be accessed via this website'
            elif error_code == 'Expired':
                error_message = 'Sorry, %s is no longer available.' % video_data.get('title', '')
            raise ExtractorError('%s said: %s' % (self.IE_NAME, error_message), expected=True)

        urls = player_params['releaseUrls']
        theplatform_url = (urls.get('progressive') or urls.get('html')
                           or urls.get('standard') or player_params['relatedItemsURL'])

        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'id': video_id,
            'url': smuggle_url(self._proto_relative_url(theplatform_url), {'force_smil_url': True}),
        }