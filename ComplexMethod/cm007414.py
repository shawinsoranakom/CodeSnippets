def add_format(f, protocol, is_preview=False):
            mobj = re.search(r'\.(?P<abr>\d+)\.(?P<ext>[0-9a-z]{3,4})(?=[/?])', stream_url)
            if mobj:
                for k, v in mobj.groupdict().items():
                    if not f.get(k):
                        f[k] = v
            format_id_list = []
            if protocol:
                format_id_list.append(protocol)
            ext = f.get('ext')
            if ext == 'aac':
                f['abr'] = '256'
            for k in ('ext', 'abr'):
                v = f.get(k)
                if v:
                    format_id_list.append(v)
            preview = is_preview or re.search(r'/(?:preview|playlist)/0/30/', f['url'])
            if preview:
                format_id_list.append('preview')
            abr = f.get('abr')
            if abr:
                f['abr'] = int(abr)
            if protocol == 'hls':
                protocol = 'm3u8' if ext == 'aac' else 'm3u8_native'
            else:
                protocol = 'http'
            f.update({
                'format_id': '_'.join(format_id_list),
                'protocol': protocol,
                'preference': -10 if preview else None,
            })
            formats.append(f)