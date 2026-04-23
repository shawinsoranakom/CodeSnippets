def _fetch_youtube_metadata(self, image_url_only=False):
        """ Fetches video metadata from the YouTube API.

        Returns a dict containing video metadata with the following keys (matching slide.slide fields):
        - 'name' matching the video title
        - 'description' matching the video description
        - 'image_1920' binary data of the video thumbnail
          OR 'image_url' containing an external link to the thumbnail when 'image_url_only' param is True
        - 'completion_time' matching the video duration
          The received duration is under a special format (e.g: PT1M21S15, meaning 1h 21m 15s).

        :param image_url_only: if True, will return 'image_url' instead of binary data
          Typically used when displaying a slide preview to the end user.
        :return a tuple (values, error) containing the values of the slide and a potential error
          (e.g: 'Video could not be found') """

        self.ensure_one()
        google_app_key = self.env['website'].get_current_website().sudo().website_slide_google_app_key
        error_message = False
        try:
            response = requests.get(
                'https://www.googleapis.com/youtube/v3/videos',
                timeout=3,
                params={
                    'fields': 'items(id,snippet,contentDetails)',
                    'id': self.youtube_id,
                    'key': google_app_key,
                    'part': 'snippet,contentDetails'
                }
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_message = e.response.content
            if 'application/json' in e.response.headers.get('content-type'):
                json_response = e.response.json()
                if json_response.get('error', {}).get('code') == 404:
                    return {}, _('Your video could not be found on YouTube, please check the link and/or privacy settings')
        except requests.exceptions.ConnectionError as e:
            error_message = str(e)

        if not error_message:
            response = response.json()
            if response.get('error'):
                error_message = response.get('error', {}).get('errors', [{}])[0].get('reason')

            if not response.get('items'):
                error_message = _('Your video could not be found on YouTube, please check the link and/or privacy settings')

        if error_message:
            _logger.warning('Could not fetch YouTube metadata: %s', error_message)
            return {}, error_message

        slide_metadata = {'slide_type': 'youtube_video'}
        youtube_values = response.get('items')[0]
        youtube_duration = youtube_values.get('contentDetails', {}).get('duration')
        if youtube_duration:
            parsed_duration = re.search(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', youtube_duration)
            if parsed_duration:
                slide_metadata['completion_time'] = (int(parsed_duration.group(1) or 0)) + \
                                                    (int(parsed_duration.group(2) or 0) / 60) + \
                                                    (round(int(parsed_duration.group(3) or 0) /60) / 60)

        if youtube_values.get('snippet'):
            snippet = youtube_values['snippet']
            slide_metadata.update({
                'name': snippet['title'],
                'description': snippet['description'],
            })

            thumbnail_url = snippet['thumbnails']['high']['url']
            if image_url_only:
                slide_metadata['image_url'] = thumbnail_url
            else:
                slide_metadata['image_1920'] = base64.b64encode(
                    requests.get(thumbnail_url, timeout=3).content
                )

        return slide_metadata, None