def _fetch_google_drive_metadata(self, image_url_only=False):
        """ Fetches document / video metadata from the Google Drive API.

        Returns a dict containing metadata with the following keys (matching slide.slide fields):
        - 'name' matching the external file title
        - 'image_1920' binary data of the file thumbnail
          OR 'image_url' containing an external link to the thumbnail when 'image_url_only' param is True
        - 'completion_time' which is computed for 2 types of files:
          - pdf files where we download the content and then use slide.slide#_get_completion_time_pdf()
          - videos where we use the 'videoMediaMetadata' to extract the 'durationMillis'

        :param image_url_only: if True, will return 'image_url' instead of binary data
          Typically used when displaying a slide preview to the end user.
        :return a tuple (values, error) containing the values of the slide and a potential error
          (e.g: 'File could not be found') """

        params = {}
        params['projection'] = 'BASIC'
        params['supportsAllDrives'] = 'true'  # Allow Shared Drive links
        if 'google.drive.config' in self.env:
            access_token = False
            try:
                access_token = self.env['google.drive.config'].get_access_token()
            except (RedirectWarning, UserError):
                pass  # ignore and use the 'key' fallback

            if access_token:
                params['access_token'] = access_token

        if not params.get('access_token'):
            params['key'] = self.env['website'].get_current_website().sudo().website_slide_google_app_key

        error_message = False
        try:
            response = requests.get(
                'https://www.googleapis.com/drive/v2/files/%s' % self.google_drive_id,
                timeout=3,
                params=params
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_message = e.response.content
            if 'application/json' in e.response.headers.get('content-type'):
                json_response = e.response.json()
                if json_response.get('error', {}).get('code') == 404:
                    # in case we don't find the file on GDrive, we want to give some feedback to our user
                    return {}, _('Your file could not be found on Google Drive, please check the link and/or privacy settings')
        except requests.exceptions.ConnectionError as e:
            error_message = str(e)

        if not error_message:
            response = response.json()
            if response.get('error'):
                error_message = response.get('error', {}).get('errors', [{}])[0].get('reason')

        if error_message:
            _logger.warning('Could not fetch Google Drive metadata: %s', error_message)
            return {}, error_message

        google_drive_values = response
        slide_metadata = {
            'name': google_drive_values.get('title')
        }

        if google_drive_values.get('thumbnailLink'):
            # small trick, we remove '=s220' to get a higher definition
            thumbnail_url = google_drive_values['thumbnailLink'].replace('=s220', '')
            if image_url_only:
                slide_metadata['image_url'] = thumbnail_url
            else:
                slide_metadata['image_1920'] = base64.b64encode(
                    requests.get(thumbnail_url, timeout=3).content
                )

        if self.slide_category == 'document':
            sheet_mimetypes = [
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.oasis.opendocument.spreadsheet',
                'application/vnd.google-apps.spreadsheet'
            ]

            doc_mimetypes = [
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.oasis.opendocument.text',
                'application/vnd.google-apps.document'
            ]

            slides_mimetypes = [
                'application/vnd.ms-powerpoint',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'application/vnd.oasis.opendocument.presentation',
                'application/vnd.google-apps.presentation'
            ]

            mime_type = google_drive_values.get('mimeType')
            if mime_type == 'application/pdf':
                slide_metadata['slide_type'] = 'pdf'
                if google_drive_values.get('downloadUrl'):
                    # attempt to download PDF content to extract a completion_time based on the number of pages
                    try:
                        pdf_response = requests.get(google_drive_values.get('downloadUrl'), timeout=5)
                        completion_time = self._get_completion_time_pdf(pdf_response.content)
                        if completion_time:
                            slide_metadata['completion_time'] = completion_time
                    except Exception:
                        pass  # fail silently as this is nice to have
            elif mime_type in sheet_mimetypes:
                slide_metadata['slide_type'] = 'sheet'
            elif mime_type in doc_mimetypes:
                slide_metadata['slide_type'] = 'doc'
            elif mime_type in slides_mimetypes:
                slide_metadata['slide_type'] = 'slides'
            elif mime_type and mime_type.startswith('image/'):
                # image and videos should be input using another "slide_category" but let's be nice and
                # assign them a matching slide_type
                slide_metadata['slide_type'] = 'image'
            elif mime_type and mime_type.startswith('video/'):
                slide_metadata['slide_type'] = 'google_drive_video'

        elif self.slide_category == 'video':
            completion_time = round(float(
                google_drive_values.get('videoMediaMetadata', {}).get('durationMillis', 0)
                ) / (60 * 1000)) / 60  # millis to hours conversion rounded to the minute
            if completion_time:
                slide_metadata['completion_time'] = completion_time

        return slide_metadata, None