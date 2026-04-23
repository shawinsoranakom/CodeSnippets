def handle_endtag(self, tag):
        "Handle endtags in help.html."
        if tag in ['h1', 'h2', 'h3']:
            assert self.level == 0
            indent = ('        ' if tag == 'h3' else
                      '    ' if tag == 'h2' else
                      '')
            self.toc.append((indent+self.header, self.text.index('insert')))
            self.tags = ''
        elif tag in ['span', 'em']:
            self.chartags = ''
        elif tag == 'a':
            self.hdrlink = False
        elif tag == 'pre':
            self.pre = False
            self.tags = ''
        elif tag in ['ul', 'dd', 'ol']:
            self.indent(-1)
        self.prevtag = (False, tag)