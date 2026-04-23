def format_resolution(format, default='unknown'):
        if format.get('vcodec') == 'none' and format.get('acodec') != 'none':
            return 'audio only'
        if format.get('resolution') is not None:
            return format['resolution']
        if format.get('width') and format.get('height'):
            return '%dx%d' % (format['width'], format['height'])
        elif format.get('height'):
            return '{}p'.format(format['height'])
        elif format.get('width'):
            return '%dx?' % format['width']
        return default