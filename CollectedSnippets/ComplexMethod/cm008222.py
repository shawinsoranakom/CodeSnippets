def _get_video_src(self, video):
        for source in traverse_obj(video, (
                'mediaProfile', 'mediaFile', lambda _, v: v.get('mimeType'))):
            url = source['value']
            for s, r in (
                ('media2vam.corriere.it.edgesuite.net', 'media2vam-corriere-it.akamaized.net'),
                ('media.youreporter.it.edgesuite.net', 'media-youreporter-it.akamaized.net'),
                ('corrierepmd.corriere.it.edgesuite.net', 'corrierepmd-corriere-it.akamaized.net'),
                ('media2vam-corriere-it.akamaized.net/fcs.quotidiani/vr/videos/', 'video.corriere.it/vr360/videos/'),
                ('http://', 'https://'),
            ):
                url = url.replace(s, r)

            type_ = mimetype2ext(source['mimeType'])
            if type_ == 'm3u8' and '-vh.akamaihd' in url:
                # still needed for some old content: see _TESTS #3
                matches = re.search(r'(?:https?:)?//(?P<host>[\w\.\-]+)\.net/i(?P<path>.+)$', url)
                if matches:
                    url = f'https://vod.rcsobjects.it/hls/{self._MIGRATION_MAP[matches.group("host")]}{matches.group("path")}'
            if traverse_obj(video, ('mediaProfile', 'geoblocking')) or (
                    type_ == 'm3u8' and 'fcs.quotidiani_!' in url):
                url = url.replace('vod.rcsobjects', 'vod-it.rcsobjects')
            if type_ == 'm3u8' and 'vod' in url:
                url = url.replace('.csmil', '.urlset')
            if type_ == 'mp3':
                url = url.replace('media2vam-corriere-it.akamaized.net', 'vod.rcsobjects.it/corriere')

            yield {
                'type': type_,
                'url': url,
                'bitrate': source.get('bitrate'),
            }