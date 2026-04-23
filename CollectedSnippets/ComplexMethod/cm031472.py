def handle_starttag(self, tag, attrs):
        "Handle starttags in help.html."
        class_ = ''
        for a, v in attrs:
            if a == 'class':
                class_ = v
        s = ''
        if tag == 'p' and self.prevtag and not self.prevtag[0]:
            # Begin a new block for <p> tags after a closed tag.
            # Avoid extra lines, e.g. after <pre> tags.
            lastline = self.text.get('end-1c linestart', 'end-1c')
            s = '\n\n' if lastline and not lastline.isspace() else '\n'
        elif tag == 'span' and class_ == 'pre':
            self.chartags = 'pre'
        elif tag == 'span' and class_ == 'versionmodified':
            self.chartags = 'em'
        elif tag == 'em':
            self.chartags = 'em'
        elif tag in ['ul', 'ol']:
            if class_.find('simple') != -1:
                s = '\n'
                self.simplelist = True
            else:
                self.simplelist = False
            self.indent()
        elif tag == 'dl':
            if self.level > 0:
                self.nested_dl = True
        elif tag == 'li':
            s = '\n* '
        elif tag == 'dt':
            s = '\n\n' if not self.nested_dl else '\n'  # Avoid extra line.
            self.nested_dl = False
        elif tag == 'dd':
            self.indent()
            s = '\n'
        elif tag == 'pre':
            self.pre = True
            self.text.insert('end', '\n\n')
            self.tags = 'preblock'
        elif tag == 'a' and class_ == 'headerlink':
            self.hdrlink = True
        elif tag == 'h1':
            self.tags = tag
        elif tag in ['h2', 'h3']:
            self.header = ''
            self.text.insert('end', '\n\n')
            self.tags = tag
        self.text.insert('end', s, (self.tags, self.chartags))
        self.prevtag = (True, tag)