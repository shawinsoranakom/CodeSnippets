def handle_data(self, data):
        "Handle date segments in help.html."
        if not self.hdrlink:
            d = data if self.pre else data.replace('\n', ' ')
            if self.tags == 'h1':
                try:
                    self.hprefix = d[:d.index(' ')]
                    if not self.hprefix.isdigit():
                        self.hprefix = ''
                except ValueError:
                    self.hprefix = ''
            if self.tags in ['h1', 'h2', 'h3']:
                if (self.hprefix != '' and
                    d[0:len(self.hprefix)] == self.hprefix):
                    d = d[len(self.hprefix):]
                self.header += d.strip()
            self.text.insert('end', d, (self.tags, self.chartags))