def _extract_vrv_formats(self, url, video_id, stream_format, audio_lang, hardsub_lang):
        if not url or stream_format not in ('hls', 'dash', 'adaptive_hls'):
            return []
        stream_id_list = []
        if audio_lang:
            stream_id_list.append('audio-%s' % audio_lang)
        if hardsub_lang:
            stream_id_list.append('hardsub-%s' % hardsub_lang)
        format_id = stream_format
        if stream_id_list:
            format_id += '-' + '-'.join(stream_id_list)
        if 'hls' in stream_format:
            adaptive_formats = self._extract_m3u8_formats(
                url, video_id, 'mp4', m3u8_id=format_id,
                note='Downloading %s information' % format_id,
                fatal=False)
        elif stream_format == 'dash':
            adaptive_formats = self._extract_mpd_formats(
                url, video_id, mpd_id=format_id,
                note='Downloading %s information' % format_id,
                fatal=False)
        if audio_lang:
            for f in adaptive_formats:
                if f.get('acodec') != 'none':
                    f['language'] = audio_lang
        return adaptive_formats