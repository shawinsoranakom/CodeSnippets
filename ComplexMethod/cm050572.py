def prepare_preview(self, channel_id, slide_category, url=None):
        """ Will attempt to fetch external metadata for this slide from the correct
        source (YouTube, Google Drive, ...).

        To take advantage of the slide business method, we create a temporary slide record before
        fetching the metadata.
        This allows a lot of code simplification, since we use "new", it will not created anything
        in database. """

        if not url:
            return {}

        Slide = request.env['slide.slide']

        additional_values = {}
        if slide_category == 'video':
            identical_video = request.env['slide.slide']
            existing_videos = Slide.search([
                ('channel_id', '=', int(channel_id)),
                ('slide_category', '=', 'video')
            ])

            slide = Slide.new({
                'channel_id': int(channel_id),
                'name': 'memory_record_for_computed_fields',
                'slide_category': 'video',
                'url': url
            })

            if not slide.video_source_type:
                return {'error': _("Could not find your video. Please check if your link is correct and if the video can be accessed.")}

            if slide.video_source_type == 'youtube':
                identical_video = existing_videos.filtered(
                    lambda existing_video: slide.youtube_id == existing_video.youtube_id)
            elif slide.video_source_type == 'google_drive':
                identical_video = existing_videos.filtered(
                    lambda existing_video: slide.google_drive_id == existing_video.google_drive_id)
            elif slide.video_source_type == 'vimeo':
                identical_video = existing_videos.filtered(
                    lambda existing_video: slide.vimeo_id == existing_video.vimeo_id)
            if identical_video:
                identical_video_name = identical_video[0].name
                additional_values['info'] = _('This video already exists in this channel on the following content: %s', identical_video_name)
        elif slide_category in ['document', 'infographic']:
            slide = Slide.new({
                'channel_id': int(channel_id),
                'name': 'memory_record_for_computed_fields',
                'slide_category': slide_category,
                'source_type': 'external',
                'url': url
            })

            if not slide.google_drive_id:
                return {'error': _('Please enter valid Google Drive Link')}

        slide_values, error = slide._fetch_external_metadata(image_url_only=True)
        if error:
            return {'error': error}

        if additional_values:
            slide_values.update(additional_values)

        return slide_values