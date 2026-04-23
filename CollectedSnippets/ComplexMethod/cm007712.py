def _parse_mp4(self, metadata):
        video_formats = []
        video_root = None

        mp4_video = xpath_text(metadata, './mp4video', default=None)
        if mp4_video is not None:
            mobj = re.match(r'(?P<root>https?://.*?/).*', mp4_video)
            video_root = mobj.group('root')
        if video_root is None:
            http_host = xpath_text(metadata, 'httpHost', default=None)
            if http_host:
                video_root = 'http://%s/' % http_host
        if video_root is None:
            # Hard-coded in http://evt.dispeak.com/ubm/gdc/sf16/custom/player2.js
            # Works for GPUTechConf, too
            video_root = 'http://s3-2u.digitallyspeaking.com/'

        formats = metadata.findall('./MBRVideos/MBRVideo')
        if not formats:
            return None
        for a_format in formats:
            stream_name = xpath_text(a_format, 'streamName', fatal=True)
            video_path = re.match(r'mp4\:(?P<path>.*)', stream_name).group('path')
            url = video_root + video_path
            bitrate = xpath_text(a_format, 'bitrate')
            tbr = int_or_none(bitrate)
            vbr = int_or_none(self._search_regex(
                r'-(\d+)\.mp4', video_path, 'vbr', default=None))
            abr = tbr - vbr if tbr and vbr else None
            video_formats.append({
                'format_id': bitrate,
                'url': url,
                'tbr': tbr,
                'vbr': vbr,
                'abr': abr,
            })
        return video_formats