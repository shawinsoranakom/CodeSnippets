def _default_format_spec(self, info_dict):
        prefer_best = (
            self.params['outtmpl']['default'] == '-'
            or (info_dict.get('is_live') and not self.params.get('live_from_start')))

        def can_merge():
            merger = FFmpegMergerPP(self)
            return merger.available and merger.can_merge()

        if not prefer_best and not can_merge():
            prefer_best = True
            formats = self._get_formats(info_dict)
            evaluate_formats = lambda spec: self._select_formats(formats, self.build_format_selector(spec))
            if evaluate_formats('b/bv+ba') != evaluate_formats('bv*+ba/b'):
                self.report_warning('ffmpeg not found. The downloaded format may not be the best available. '
                                    'Installing ffmpeg is strongly recommended: https://github.com/yt-dlp/yt-dlp#dependencies')

        compat = (self.params.get('allow_multiple_audio_streams')
                  or 'format-spec' in self.params['compat_opts'])

        return ('best/bestvideo+bestaudio' if prefer_best
                else 'bestvideo+bestaudio/best' if compat
                else 'bestvideo*+bestaudio/best')