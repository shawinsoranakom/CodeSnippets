def _fetch_vimeo_metadata(self, image_url_only=False):
        """ Fetches video metadata from the Vimeo API.
        See https://developer.vimeo.com/api/oembed/showcases for more information.

        Returns a dict containing video metadata with the following keys (matching slide.slide fields):
        - 'name' matching the video title
        - 'description' matching the video description
        - 'image_1920' binary data of the video thumbnail
          OR 'image_url' containing an external link to the thumbnail when 'fetch_image' param is False
        - 'completion_time' matching the video duration

        :param image_url_only: if False, will return 'image_url' instead of binary data
          Typically used when displaying a slide preview to the end user.
        :return a tuple (values, error) containing the values of the slide and a potential error
          (e.g: 'Video could not be found') """

        self.ensure_one()
        error_message = False
        try:
            response = requests.get(
                'https://vimeo.com/api/oembed.json?%s' % urls.url_encode({'url': self.video_url}),
                timeout=3
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_message = e.response.content
            if e.response.status_code == 404:
                return {}, _('Your video could not be found on Vimeo, please check the link and/or privacy settings')
        except requests.exceptions.ConnectionError as e:
            error_message = str(e)

        if not error_message and 'application/json' in response.headers.get('content-type'):
            response = response.json()
            if response.get('error'):
                error_message = response.get('error', {}).get('errors', [{}])[0].get('reason')

            if not response:
                error_message = _('Please enter a valid Vimeo video link')

        if error_message:
            _logger.warning('Could not fetch Vimeo metadata: %s', error_message)
            return {}, error_message

        vimeo_values = response
        slide_metadata = {'slide_type': 'vimeo_video'}

        if vimeo_values.get('title'):
            slide_metadata['name'] = vimeo_values.get('title')

        if vimeo_values.get('description'):
            slide_metadata['description'] = vimeo_values.get('description')

        if vimeo_values.get('duration'):
            # seconds to hours conversion
            slide_metadata['completion_time'] = round(vimeo_values.get('duration') / 60) / 60

        thumbnail_url = vimeo_values.get('thumbnail_url')
        if thumbnail_url:
            if image_url_only:
                slide_metadata['image_url'] = thumbnail_url
            else:
                slide_metadata['image_1920'] = base64.b64encode(
                    requests.get(thumbnail_url, timeout=3).content
                )

        return slide_metadata, None