def _real_extract(self, url):
        video_id = self._match_id(url)
        asset = self._download_json(url, video_id)['asset']

        if asset.get('drm') not in ('NonDRM', None):
            self.report_drm(video_id)

        content_type = asset.get('type')
        if content_type and content_type != 'video':
            self.report_warning(f'Unknown content type: {content_type}' + bug_reports_message(), video_id)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(asset['streamingUrl'], video_id)

        audio_streaming_url = traverse_obj(
            asset, 'palyoutPathAudio', 'playoutpathaudio', expected_type=str)
        if audio_streaming_url:
            audio_formats = self._extract_m3u8_formats(audio_streaming_url, video_id, fatal=False, ext='mp3')
            for audio_format in audio_formats:
                # all the audio streams appear to be aac
                audio_format.setdefault('vcodec', 'none')
                audio_format.setdefault('acodec', 'aac')
                formats.append(audio_format)

        return {
            'id': video_id,
            'title': asset.get('title'),
            'description': asset.get('description'),
            'duration': float_or_none(asset.get('duration')),
            'timestamp': unified_timestamp(asset.get('dateadded')),
            'channel': asset.get('brand'),
            'thumbnails': [{'url': thumbnail_url} for thumbnail_url in asset.get('thumbnails') or []],
            'formats': formats,
            'subtitles': subtitles,
        }