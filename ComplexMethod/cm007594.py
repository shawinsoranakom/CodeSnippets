def _webpage_read_content(self, urlh, url_or_request, video_id, note=None, errnote=None, fatal=True, prefix=None, encoding=None):
        content_type = urlh.headers.get('Content-Type', '')
        webpage_bytes = urlh.read()
        if prefix is not None:
            webpage_bytes = prefix + webpage_bytes
        if not encoding:
            encoding = self._guess_encoding_from_content(content_type, webpage_bytes)
        if self.get_param('dump_intermediate_pages', False):
            self.to_screen('Dumping request to ' + urlh.geturl())
            dump = base64.b64encode(webpage_bytes).decode('ascii')
            self.to_screen(dump)
        if self.get_param('write_pages', False):
            basen = '%s_%s' % (video_id, urlh.geturl())
            if len(basen) > 240:
                h = '___' + hashlib.md5(basen.encode('utf-8')).hexdigest()
                basen = basen[:240 - len(h)] + h
            raw_filename = basen + '.dump'
            filename = sanitize_filename(raw_filename, restricted=True)
            self.to_screen('Saving request to ' + filename)
            # Working around MAX_PATH limitation on Windows (see
            # http://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx)
            if compat_os_name == 'nt':
                absfilepath = os.path.abspath(filename)
                if len(absfilepath) > 259:
                    filename = '\\\\?\\' + absfilepath
            with open(filename, 'wb') as outf:
                outf.write(webpage_bytes)

        try:
            content = webpage_bytes.decode(encoding, 'replace')
        except LookupError:
            content = webpage_bytes.decode('utf-8', 'replace')

        self.__check_blocked(content)

        return content