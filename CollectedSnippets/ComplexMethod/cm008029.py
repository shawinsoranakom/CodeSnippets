def _format_note(self, fdict):
        res = ''
        if fdict.get('ext') in ['f4f', 'f4m']:
            res += '(unsupported)'
        if fdict.get('language'):
            if res:
                res += ' '
            res += '[{}]'.format(fdict['language'])
        if fdict.get('format_note') is not None:
            if res:
                res += ' '
            res += fdict['format_note']
        if fdict.get('tbr') is not None:
            if res:
                res += ', '
            res += '%4dk' % fdict['tbr']
        if fdict.get('container') is not None:
            if res:
                res += ', '
            res += '{} container'.format(fdict['container'])
        if (fdict.get('vcodec') is not None
                and fdict.get('vcodec') != 'none'):
            if res:
                res += ', '
            res += fdict['vcodec']
            if fdict.get('vbr') is not None:
                res += '@'
        elif fdict.get('vbr') is not None and fdict.get('abr') is not None:
            res += 'video@'
        if fdict.get('vbr') is not None:
            res += '%4dk' % fdict['vbr']
        if fdict.get('fps') is not None:
            if res:
                res += ', '
            res += '{}fps'.format(fdict['fps'])
        if fdict.get('acodec') is not None:
            if res:
                res += ', '
            if fdict['acodec'] == 'none':
                res += 'video only'
            else:
                res += '%-5s' % fdict['acodec']
        elif fdict.get('abr') is not None:
            if res:
                res += ', '
            res += 'audio'
        if fdict.get('abr') is not None:
            res += '@%3dk' % fdict['abr']
        if fdict.get('asr') is not None:
            res += ' (%5dHz)' % fdict['asr']
        if fdict.get('filesize') is not None:
            if res:
                res += ', '
            res += format_bytes(fdict['filesize'])
        elif fdict.get('filesize_approx') is not None:
            if res:
                res += ', '
            res += '~' + format_bytes(fdict['filesize_approx'])
        return res