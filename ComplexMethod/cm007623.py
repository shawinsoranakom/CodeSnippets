def _create_http_urls(self, relinker_url, fmts):
        _RELINKER_REG = r'https?://(?P<host>[^/]+?)/(?:i/)?(?P<extra>[^/]+?)/(?P<path>.+?)/(?P<id>\w+)(?:_(?P<quality>[\d\,]+))?(?:\.mp4|/playlist\.m3u8).+?'
        _MP4_TMPL = '%s&overrideUserAgentRule=mp4-%s'
        _QUALITY = {
            # tbr: w, h
            '250': [352, 198],
            '400': [512, 288],
            '700': [512, 288],
            '800': [700, 394],
            '1200': [736, 414],
            '1800': [1024, 576],
            '2400': [1280, 720],
            '3200': [1440, 810],
            '3600': [1440, 810],
            '5000': [1920, 1080],
            '10000': [1920, 1080],
        }

        def test_url(url):
            resp = self._request_webpage(
                HEADRequest(url), None, headers={'User-Agent': 'Rai'},
                fatal=False, errnote=False, note=False)

            if resp is False:
                return False

            if resp.code == 200:
                return False if resp.url == url else resp.url
            return None

        def get_format_info(tbr):
            import math
            br = int_or_none(tbr)
            if len(fmts) == 1 and not br:
                br = fmts[0].get('tbr')
            if br > 300:
                tbr = compat_str(math.floor(br / 100) * 100)
            else:
                tbr = '250'

            # try extracting info from available m3u8 formats
            format_copy = None
            for f in fmts:
                if f.get('tbr'):
                    br_limit = math.floor(br / 100)
                    if br_limit - 1 <= math.floor(f['tbr'] / 100) <= br_limit + 1:
                        format_copy = f.copy()
            return {
                'width': format_copy.get('width'),
                'height': format_copy.get('height'),
                'tbr': format_copy.get('tbr'),
                'vcodec': format_copy.get('vcodec'),
                'acodec': format_copy.get('acodec'),
                'fps': format_copy.get('fps'),
                'format_id': 'https-%s' % tbr,
            } if format_copy else {
                'width': _QUALITY[tbr][0],
                'height': _QUALITY[tbr][1],
                'format_id': 'https-%s' % tbr,
                'tbr': int(tbr),
            }

        loc = test_url(_MP4_TMPL % (relinker_url, '*'))
        if not isinstance(loc, compat_str):
            return []

        mobj = re.match(
            _RELINKER_REG,
            test_url(relinker_url) or '')
        if not mobj:
            return []

        available_qualities = mobj.group('quality').split(',') if mobj.group('quality') else ['*']
        available_qualities = [i for i in available_qualities if i]

        formats = []
        for q in available_qualities:
            fmt = {
                'url': _MP4_TMPL % (relinker_url, q),
                'protocol': 'https',
                'ext': 'mp4',
            }
            fmt.update(get_format_info(q))
            formats.append(fmt)
        return formats