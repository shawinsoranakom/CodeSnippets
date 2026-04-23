def _extract_free_formats(self, video, video_id):
        stream_data = video['streamdata']
        cdn = stream_data['cdnType']
        assert cdn == 'free'

        hash = video['general']['hash']

        ps = compat_str(stream_data['originalDomain'])
        if stream_data['applyFolderHierarchy'] == 1:
            s = ('%04d' % int(video_id))[::-1]
            ps += '/%s/%s' % (s[0:2], s[2:4])
        ps += '/%s/%s_' % (video_id, hash)

        t = 'http://%s' + ps
        fd = stream_data['azureFileDistribution'].split(',')
        cdn_provider = stream_data['cdnProvider']

        def p0(p):
            return '_%s' % p if stream_data['applyAzureStructure'] == 1 else ''

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
                filename = '%s%s%s.mp4' % (h, p[1], p0(tbr))
                f = {
                    'url': http_base + '/' + filename,
                    'format_id': '%s-http-%d' % (cdn, tbr),
                    'tbr': tbr,
                }
                width_height = p[1].split('x')
                if len(width_height) == 2:
                    f.update({
                        'width': int_or_none(width_height[0]),
                        'height': int_or_none(width_height[1]),
                    })
                formats.append(f)
                a = filename + ':%s' % (tbr * 1000)
                t += a + ','
            t = t[:-1] + '&audiostream=' + a.split(':')[0]
        else:
            assert False

        if cdn_provider == 'ce':
            formats.extend(self._extract_mpd_formats(
                t % (stream_data['cdnPathDASH'], 'mpd'), video_id,
                mpd_id='%s-dash' % cdn, fatal=False))
        formats.extend(self._extract_m3u8_formats(
            t % (stream_data['cdnPathHLS'], 'm3u8'), video_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id='%s-hls' % cdn, fatal=False))

        return formats