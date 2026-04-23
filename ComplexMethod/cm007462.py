def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_meta(
            ['twitter:title', 'og:title'], webpage, fatal=True)
        player_data = re.findall(
            r"PlayerFactory\.setParam\('(?P<type>format|param)',\s*'(?P<name>[^']+)',\s*'(?P<val>[^']+)'\);",
            webpage)

        formats = []
        duration = thumb = None
        for t, n, v in player_data:
            if t == 'format':
                if n in ('video-hds-vod-ec', 'video-hls-vod-ec', 'video-viralize', 'video-youtube-pfp'):
                    continue
                elif n.endswith('-vod-ak'):
                    formats.extend(self._extract_akamai_formats(
                        v, video_id, {'http': 'media.gedidigital.it'}))
                else:
                    ext = determine_ext(v)
                    if ext == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            v, video_id, 'mp4', 'm3u8_native', m3u8_id=n, fatal=False))
                        continue
                    f = {
                        'format_id': n,
                        'url': v,
                    }
                    if ext == 'mp3':
                        abr = int_or_none(self._search_regex(
                            r'-mp3-audio-(\d+)', v, 'abr', default=None))
                        f.update({
                            'abr': abr,
                            'tbr': abr,
                            'vcodec': 'none'
                        })
                    else:
                        mobj = re.match(r'^video-rrtv-(\d+)(?:-(\d+))?$', n)
                        if mobj:
                            f.update({
                                'height': int(mobj.group(1)),
                                'vbr': int_or_none(mobj.group(2)),
                            })
                        if not f.get('vbr'):
                            f['vbr'] = int_or_none(self._search_regex(
                                r'-video-rrtv-(\d+)', v, 'abr', default=None))
                    formats.append(f)
            elif t == 'param':
                if n in ['image_full', 'image']:
                    thumb = v
                elif n == 'videoDuration':
                    duration = int_or_none(v)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta(
                ['twitter:description', 'og:description', 'description'], webpage),
            'thumbnail': thumb or self._og_search_thumbnail(webpage),
            'formats': formats,
            'duration': duration,
        }