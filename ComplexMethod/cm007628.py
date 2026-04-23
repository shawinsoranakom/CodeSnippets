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