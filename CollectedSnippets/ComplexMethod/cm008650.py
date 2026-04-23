def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        track_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        playables = self._parse_json(
            self._search_regex(
                r'window\.Playables\s*=\s*({.+?});', webpage,
                'playables info', flags=re.DOTALL),
            track_id)

        track = next(t for t in playables['tracks'] if t['id'] == int(track_id))

        title = ', '.join(a['name'] for a in track['artists']) + ' - ' + track['name']
        if track['mix']:
            title += ' (' + track['mix'] + ')'

        formats = []
        for ext, info in track['preview'].items():
            if not info['url']:
                continue
            fmt = {
                'url': info['url'],
                'ext': ext,
                'format_id': ext,
                'vcodec': 'none',
            }
            if ext == 'mp3':
                fmt['acodec'] = 'mp3'
                fmt['abr'] = 96
                fmt['asr'] = 44100
            elif ext == 'mp4':
                fmt['acodec'] = 'aac'
                fmt['abr'] = 96
                fmt['asr'] = 44100
            formats.append(fmt)

        images = []
        for name, info in track['images'].items():
            image_url = info.get('url')
            if name == 'dynamic' or not image_url:
                continue
            image = {
                'id': name,
                'url': image_url,
                'height': int_or_none(info.get('height')),
                'width': int_or_none(info.get('width')),
            }
            images.append(image)

        return {
            'id': str(track.get('id')) or track_id,
            'display_id': track.get('slug') or display_id,
            'title': title,
            'formats': formats,
            'thumbnails': images,
        }