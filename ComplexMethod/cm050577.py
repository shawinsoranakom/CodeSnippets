def _compute_slide_type(self):
        """ For 'local content' or specific slide categories, the slide type is directly derived
        from the slide category.

        For external content, the slide type is determined from the metadata and the mime_type.
        (See #_fetch_google_drive_metadata() for more details)."""

        for slide in self:
            if slide.slide_category == 'document':
                if slide.source_type == 'local_file':
                    slide.slide_type = 'pdf'
                elif slide.slide_type not in ['pdf', 'sheet', 'doc', 'slides']:
                    slide.slide_type = False
            elif slide.slide_category == 'infographic':
                slide.slide_type = 'image'
            elif slide.slide_category == 'article':
                slide.slide_type = 'article'
            elif slide.slide_category == 'quiz':
                slide.slide_type = 'quiz'
            elif slide.slide_category == 'video' and slide.video_source_type == 'youtube':
                slide.slide_type = 'youtube_video'
            elif slide.slide_category == 'video' and slide.video_source_type == 'google_drive':
                slide.slide_type = 'google_drive_video'
            elif slide.slide_category == 'video' and slide.video_source_type == 'vimeo':
                slide.slide_type = 'vimeo_video'
            else:
                slide.slide_type = False