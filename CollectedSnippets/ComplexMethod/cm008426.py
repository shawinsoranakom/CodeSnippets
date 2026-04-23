def get_format_info(tbr):
            import math
            br = int_or_none(tbr)
            if len(fmts) == 1 and not br:
                br = fmts[0].get('tbr')
            if br and br > 300:
                tbr = math.floor(br / 100) * 100
            else:
                tbr = 250

            # try extracting info from available m3u8 formats
            format_copy = [None, None]
            for f in fmts:
                if f.get('tbr'):
                    if percentage(tbr, f['tbr']):
                        format_copy[0] = f.copy()
                if [f.get('width'), f.get('height')] == _QUALITY.get(tbr):
                    format_copy[1] = f.copy()
                    format_copy[1]['tbr'] = tbr

            # prefer format with similar bitrate because there might be
            # multiple video with the same resolution but different bitrate
            format_copy = format_copy[0] or format_copy[1] or {}
            return {
                'format_id': f'https-{tbr}',
                'width': format_copy.get('width'),
                'height': format_copy.get('height'),
                'tbr': format_copy.get('tbr') or tbr,
                'vcodec': format_copy.get('vcodec') or 'avc1',
                'acodec': format_copy.get('acodec') or 'mp4a',
                'fps': format_copy.get('fps') or 25,
            } if format_copy else {
                'format_id': f'https-{tbr}',
                'width': _QUALITY[tbr][0],
                'height': _QUALITY[tbr][1],
                'tbr': tbr,
                'vcodec': 'avc1',
                'acodec': 'mp4a',
                'fps': 25,
            }