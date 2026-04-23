def _extract_free_formats(self, video, video_id):
        stream_data = video['streamdata']
        cdn = stream_data['cdnType']
        assert cdn == 'free'

        video_hash = video['general']['hash']

        ps = str(stream_data['originalDomain'])
        if stream_data['applyFolderHierarchy'] == 1:
            s = ('%04d' % int(video_id))[::-1]
            ps += f'/{s[0:2]}/{s[2:4]}'
        ps += f'/{video_id}/{video_hash}_'

        t = 'http://%s' + ps
        fd = stream_data['azureFileDistribution'].split(',')
        cdn_provider = stream_data['cdnProvider']

        def p0(p):
            return f'_{p}' if stream_data['applyAzureStructure'] == 1 else ''

        formats = []
        if cdn_provider == 'ak':
            t += ','
            for i in fd:
                p = i.split(':')
                t += p[1] + p0(int(p[0])) + ','
            t += '.mp4.csmil/master.%s'
        elif cdn_provider == 'ce':
            k = t.split('/')
            h = k.pop()
            http_base = t = '/'.join(k)
            http_base = http_base % stream_data['cdnPathHTTP']
            t += '/asset.ism/manifest.%s?dcp_ver=aos4&videostream='
            for i in fd:
                p = i.split(':')
                tbr = int(p[0])
                filename = f'{h}{p[1]}{p0(tbr)}.mp4'
                f = {
                    'url': http_base + '/' + filename,
                    'format_id': f'{cdn}-http-{tbr}',
                    'tbr': tbr,
                }
                width_height = p[1].split('x')
                if len(width_height) == 2:
                    f.update({
                        'width': int_or_none(width_height[0]),
                        'height': int_or_none(width_height[1]),
                    })
                formats.append(f)
                a = filename + f':{tbr * 1000}'
                t += a + ','
            t = t[:-1] + '&audiostream=' + a.split(':')[0]
        else:
            assert False

        if cdn_provider == 'ce':
            formats.extend(self._extract_mpd_formats(
                t % (stream_data['cdnPathDASH'], 'mpd'), video_id,
                mpd_id=f'{cdn}-dash', fatal=False))
        formats.extend(self._extract_m3u8_formats(
            t % (stream_data['cdnPathHLS'], 'm3u8'), video_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id=f'{cdn}-hls', fatal=False))

        return formats