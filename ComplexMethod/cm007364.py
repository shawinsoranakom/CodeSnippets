def _format_note(self, fdict):

        def simplified_codec(f, field):
            assert field in ('acodec', 'vcodec')
            codec = f.get(field)
            return (
                'unknown' if not codec
                else '.'.join(codec.split('.')[:4]) if codec != 'none'
                else 'images' if field == 'vcodec' and f.get('acodec') == 'none'
                else None if field == 'acodec' and f.get('vcodec') == 'none'
                else 'audio only' if field == 'vcodec'
                else 'video only')

        res = join_nonempty(
            fdict.get('ext') in ('f4f', 'f4m') and '(unsupported)',
            fdict.get('language') and ('[%s]' % (fdict['language'],)),
            fdict.get('format_note') is not None and fdict['format_note'],
            fdict.get('tbr') is not None and ('%4dk' % fdict['tbr']),
            delim=' ')
        res = [res] if res else []
        if fdict.get('container') is not None:
            res.append('%s container' % (fdict['container'],))
        if fdict.get('vcodec') not in (None, 'none'):
            codec = simplified_codec(fdict, 'vcodec')
            if codec and fdict.get('vbr') is not None:
                codec += '@'
        elif fdict.get('vbr') is not None and fdict.get('abr') is not None:
            codec = 'video@'
        else:
            codec = None
        codec = join_nonempty(codec, fdict.get('vbr') is not None and ('%4dk' % fdict['vbr']))
        if codec:
            res.append(codec)
        if fdict.get('fps') is not None:
            res.append('%sfps' % (fdict['fps'],))
        codec = (
            simplified_codec(fdict, 'acodec') if fdict.get('acodec') is not None
            else 'audio' if fdict.get('abr') is not None else None)
        if codec:
            res.append(join_nonempty(
                '%-4s' % (codec + (('@%3dk' % fdict['abr']) if fdict.get('abr') else ''),),
                fdict.get('asr') and '(%5dHz)' % fdict['asr'], delim=' '))
        if fdict.get('filesize') is not None:
            res.append(format_bytes(fdict['filesize']))
        elif fdict.get('filesize_approx') is not None:
            res.append('~' + format_bytes(fdict['filesize_approx']))
        return ', '.join(res)