def _fix_m3u8_formats(self, media_url, video_id):
        fmts = self._extract_m3u8_formats(
            media_url, video_id, 'mp4', m3u8_id='hls', fatal=False)

        # Fix malformed m3u8 manifests by setting audio-only/video-only formats
        for f in fmts:
            if not f.get('acodec'):
                f['acodec'] = 'mp4a'
            if not f.get('vcodec'):
                f['vcodec'] = 'avc1'
            man_url = f['url']
            if re.search(r'chunklist(?:_b\d+)*_ao[_.]', man_url):  # audio only
                f['vcodec'] = 'none'
            elif re.search(r'chunklist(?:_b\d+)*_vo[_.]', man_url):  # video only
                f['acodec'] = 'none'
            else:  # video+audio
                if f['acodec'] == 'none':
                    f['acodec'] = 'mp4a'
                if f['vcodec'] == 'none':
                    f['vcodec'] = 'avc1'

        return fmts