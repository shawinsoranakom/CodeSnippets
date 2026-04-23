def raise_no_formats(self, info, forced=False, *, msg=None):
        has_drm = info.get('_has_drm')
        ignored, expected = self.params.get('ignore_no_formats_error'), bool(msg)
        msg = msg or (has_drm and 'This video is DRM protected') or 'No video formats found!'
        if forced or not ignored:
            raise ExtractorError(msg, video_id=info['id'], ie=info['extractor'],
                                 expected=has_drm or ignored or expected)
        else:
            self.report_warning(msg)