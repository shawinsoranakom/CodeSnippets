def _extract_azure_formats(self, video, video_id):
        stream_data = video['streamdata']
        cdn = stream_data['cdnType']
        assert cdn == 'azure'

        azure_locator = stream_data['azureLocator']

        def get_cdn_shield_base(shield_type='', static=False):
            for secure in ('', 's'):
                cdn_shield = stream_data.get('cdnShield%sHTTP%s' % (shield_type, secure.upper()))
                if cdn_shield:
                    return 'http%s://%s' % (secure, cdn_shield)
            else:
                if 'fb' in stream_data['azureAccount']:
                    prefix = 'df' if static else 'f'
                else:
                    prefix = 'd' if static else 'p'
                account = int(stream_data['azureAccount'].replace('nexxplayplus', '').replace('nexxplayfb', ''))
                return 'http://nx-%s%02d.akamaized.net/' % (prefix, account)

        language = video['general'].get('language_raw') or ''

        azure_stream_base = get_cdn_shield_base()
        is_ml = ',' in language
        azure_manifest_url = '%s%s/%s_src%s.ism/Manifest' % (
            azure_stream_base, azure_locator, video_id, ('_manifest' if is_ml else '')) + '%s'

        protection_token = try_get(
            video, lambda x: x['protectiondata']['token'], compat_str)
        if protection_token:
            azure_manifest_url += '?hdnts=%s' % protection_token

        formats = self._extract_m3u8_formats(
            azure_manifest_url % '(format=m3u8-aapl)',
            video_id, 'mp4', 'm3u8_native',
            m3u8_id='%s-hls' % cdn, fatal=False)
        formats.extend(self._extract_mpd_formats(
            azure_manifest_url % '(format=mpd-time-csf)',
            video_id, mpd_id='%s-dash' % cdn, fatal=False))
        formats.extend(self._extract_ism_formats(
            azure_manifest_url % '', video_id, ism_id='%s-mss' % cdn, fatal=False))

        azure_progressive_base = get_cdn_shield_base('Prog', True)
        azure_file_distribution = stream_data.get('azureFileDistribution')
        if azure_file_distribution:
            fds = azure_file_distribution.split(',')
            if fds:
                for fd in fds:
                    ss = fd.split(':')
                    if len(ss) == 2:
                        tbr = int_or_none(ss[0])
                        if tbr:
                            f = {
                                'url': '%s%s/%s_src_%s_%d.mp4' % (
                                    azure_progressive_base, azure_locator, video_id, ss[1], tbr),
                                'format_id': '%s-http-%d' % (cdn, tbr),
                                'tbr': tbr,
                            }
                            width_height = ss[1].split('x')
                            if len(width_height) == 2:
                                f.update({
                                    'width': int_or_none(width_height[0]),
                                    'height': int_or_none(width_height[1]),
                                })
                            formats.append(f)

        return formats