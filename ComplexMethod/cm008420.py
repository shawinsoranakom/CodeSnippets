def _create_http_urls(self, manifest_url, relinker_url, fmts, video_id):
        _MANIFEST_REG = r'/(?P<id>\w+)(?:_(?P<quality>[\d\,]+))?(?:\.mp4)?(?:\.csmil)?/playlist\.m3u8'
        _MP4_TMPL = '%s&overrideUserAgentRule=mp4-%s'
        _QUALITY = {
            # tbr: w, h
            250: [352, 198],
            400: [512, 288],
            600: [512, 288],
            700: [512, 288],
            800: [700, 394],
            1200: [736, 414],
            1500: [920, 518],
            1800: [1024, 576],
            2400: [1280, 720],
            3200: [1440, 810],
            3600: [1440, 810],
            5000: [1920, 1080],
            10000: [1920, 1080],
        }

        def percentage(number, target, pc=20, roof=125):
            """check if the target is in the range of number +/- percent"""
            if not number or number < 0:
                return False
            return abs(target - number) < min(float(number) * float(pc) / 100.0, roof)

        def get_format_info(tbr):
            import math
            br = int_or_none(tbr)
            if len(fmts) == 1 and not br:
                br = fmts[0].get('tbr')
            if br and br > 300:
                tbr = math.floor(br / 100) * 100
            else:
                tbr = 250

            # try extracting info from available m3u8 formats
            format_copy = [None, None]
            for f in fmts:
                if f.get('tbr'):
                    if percentage(tbr, f['tbr']):
                        format_copy[0] = f.copy()
                if [f.get('width'), f.get('height')] == _QUALITY.get(tbr):
                    format_copy[1] = f.copy()
                    format_copy[1]['tbr'] = tbr

            # prefer format with similar bitrate because there might be
            # multiple video with the same resolution but different bitrate
            format_copy = format_copy[0] or format_copy[1] or {}
            return {
                'format_id': f'https-{tbr}',
                'width': format_copy.get('width'),
                'height': format_copy.get('height'),
                'tbr': format_copy.get('tbr') or tbr,
                'vcodec': format_copy.get('vcodec') or 'avc1',
                'acodec': format_copy.get('acodec') or 'mp4a',
                'fps': format_copy.get('fps') or 25,
            } if format_copy else {
                'format_id': f'https-{tbr}',
                'width': _QUALITY[tbr][0],
                'height': _QUALITY[tbr][1],
                'tbr': tbr,
                'vcodec': 'avc1',
                'acodec': 'mp4a',
                'fps': 25,
            }

        # Check if MP4 download is available
        try:
            self._request_webpage(
                HEADRequest(_MP4_TMPL % (relinker_url, '*')), video_id, 'Checking MP4 availability')
        except ExtractorError as e:
            self.to_screen(f'{video_id}: MP4 direct download is not available: {e.cause}')
            return []

        # filter out single-stream formats
        fmts = [f for f in fmts
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none']

        mobj = re.search(_MANIFEST_REG, manifest_url)
        if not mobj:
            return []
        available_qualities = mobj.group('quality').split(',') if mobj.group('quality') else ['*']

        formats = []
        for q in filter(None, available_qualities):
            self.write_debug(f'Creating https format for quality {q}')
            formats.append({
                'url': _MP4_TMPL % (relinker_url, q),
                'protocol': 'https',
                'ext': 'mp4',
                **get_format_info(q),
            })
        return formats