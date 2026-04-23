def send_content_range(self, total=None):
        range_header = self.headers.get('Range')
        start = end = None
        if range_header:
            mobj = re.match(r'bytes=(\d+)-(\d+)', range_header)
            if mobj:
                start, end = (int(mobj.group(i)) for i in (1, 2))
        valid_range = start is not None and end is not None
        if valid_range:
            content_range = 'bytes %d-%d' % (start, end)
            if total:
                content_range += '/%d' % total
            self.send_header('Content-Range', content_range)
        return (end - start + 1) if valid_range else total