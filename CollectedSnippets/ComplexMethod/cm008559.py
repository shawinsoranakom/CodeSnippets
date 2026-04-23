def _extract_3q_formats(self, video, video_id):
        stream_data = video['streamdata']
        cdn = stream_data['cdnType']
        assert cdn == '3q'

        q_acc, q_prefix, q_locator, q_hash = stream_data['qAccount'], stream_data['qPrefix'], stream_data['qLocator'], stream_data['qHash']
        protection_key = traverse_obj(
            video, ('protectiondata', 'key'), expected_type=str)

        def get_cdn_shield_base(shield_type=''):
            for secure in ('', 's'):
                cdn_shield = stream_data.get(f'cdnShield{shield_type}HTTP{secure.upper()}')
                if cdn_shield:
                    return f'http{secure}://{cdn_shield}'
            return f'http://sdn-global-{"prog" if shield_type.lower() == "prog" else "streaming"}-cache.3qsdn.com/' + (f's/{protection_key}/' if protection_key else '')

        stream_base = get_cdn_shield_base()

        formats = []
        formats.extend(self._extract_m3u8_formats(
            f'{stream_base}{q_acc}/files/{q_prefix}/{q_locator}/{q_acc}-{stream_data.get("qHEVCHash") or q_hash}.ism/manifest.m3u8',
            video_id, 'mp4', m3u8_id=f'{cdn}-hls', fatal=False))
        formats.extend(self._extract_mpd_formats(
            f'{stream_base}{q_acc}/files/{q_prefix}/{q_locator}/{q_acc}-{q_hash}.ism/manifest.mpd',
            video_id, mpd_id=f'{cdn}-dash', fatal=False))

        progressive_base = get_cdn_shield_base('Prog')
        q_references = stream_data.get('qReferences') or ''
        fds = q_references.split(',')
        for fd in fds:
            ss = fd.split(':')
            if len(ss) != 3:
                continue
            tbr = int_or_none(ss[1], scale=1000)
            formats.append({
                'url': f'{progressive_base}{q_acc}/uploads/{q_acc}-{ss[2]}.webm',
                'format_id': f'{cdn}-{ss[0]}{f"-{tbr}" if tbr else ""}',
                'tbr': tbr,
            })

        azure_file_distribution = stream_data.get('azureFileDistribution') or ''
        fds = azure_file_distribution.split(',')
        for fd in fds:
            ss = fd.split(':')
            if len(ss) != 3:
                continue
            tbr = int_or_none(ss[0])
            width, height = ss[1].split('x') if len(ss[1].split('x')) == 2 else (None, None)
            f = {
                'url': f'{progressive_base}{q_acc}/files/{q_prefix}/{q_locator}/{ss[2]}.mp4',
                'format_id': f'{cdn}-http-{f"-{tbr}" if tbr else ""}',
                'tbr': tbr,
                'width': int_or_none(width),
                'height': int_or_none(height),
            }
            formats.append(f)

        return formats