def extract(self, **kwargs):
        for s in self.streams:
            self.streams[s]['size'] = urls_size(self.streams[s]['src'])

        master_m3u8s = []
        for m in self.master_m3u8:
            master_m3u8s.append(self.master_m3u8[m]['url'])

        master_content = None
        master_url = None

        for master_u in master_m3u8s:
            try:
                master_content = get_content(master_u).split('\n')
            except urllib.error.URLError:
                continue
            else:
                master_url = master_u

        if master_content is None:
            return

        lines = []
        for line in master_content:
            if len(line.strip()) > 0:
                lines.append(line.strip())

        pos = 0
        while pos < len(lines):
            if lines[pos].startswith('#EXT-X-STREAM-INF'):
                patt = r'RESOLUTION=(\d+)x(\d+)'
                hit = re.search(patt, lines[pos])
                if hit is None:
                    continue
                width = hit.group(1)
                height = hit.group(2)

                if height in ('2160', '1440'):
                    m3u8_url = urllib.parse.urljoin(master_url, lines[pos+1])
                    meta = dict(m3u8_url=m3u8_url, container='m3u8')
                    if height == '1440':
                        meta['video_profile'] = '2560x1440'
                    else:
                        meta['video_profile'] = '3840x2160'
                    meta['size'] = 0
                    meta['src'] = general_m3u8_extractor(m3u8_url)
                    self.streams[height+'p'] = meta

                pos += 2
            else:
                pos += 1
        self.streams_sorted = []
        for stream_type in self.stream_types:
            if stream_type['id'] in self.streams:
                item = [('id', stream_type['id'])] + list(self.streams[stream_type['id']].items())
                self.streams_sorted.append(dict(item))