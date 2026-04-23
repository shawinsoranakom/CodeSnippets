def _compute_video_source_type(self):
        for slide in self:
            video_source_type = False
            youtube_match = re.match(self.YOUTUBE_VIDEO_ID_REGEX, slide.video_url) if slide.video_url else False
            if youtube_match and len(youtube_match.groups()) == 2 and len(youtube_match.group(2)) == 11:
                video_source_type = 'youtube'
            if slide.video_url and not video_source_type and re.match(self.GOOGLE_DRIVE_DOCUMENT_ID_REGEX, slide.video_url):
                video_source_type = 'google_drive'
            vimeo_match = re.search(self.VIMEO_VIDEO_ID_REGEX, slide.video_url) if slide.video_url else False
            if not video_source_type and vimeo_match and len(vimeo_match.groups()) == 3:
                video_source_type = 'vimeo'

            slide.video_source_type = video_source_type