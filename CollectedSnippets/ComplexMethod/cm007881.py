def _make_cmd(self, tmpfilename, info_dict):
        cmd = [self.exe, '-c',
               '--console-log-level=warn', '--summary-interval=0', '--download-result=hide',
               '--http-accept-gzip=true', '--file-allocation=none', '-x16', '-j16', '-s16']
        if 'fragments' in info_dict:
            cmd += ['--allow-overwrite=true', '--allow-piece-length-change=true']
        else:
            cmd += ['--min-split-size', '1M']

        if self.ydl.cookiejar.get_cookie_header(info_dict['url']):
            cmd += ['--load-cookies={0}'.format(self._write_cookies())]
        for key, val in self._header_items(info_dict):
            cmd += ['--header', '%s: %s' % (key, val)]
        cmd += self._configuration_args(['--max-connection-per-server', '4'])
        cmd += ['--out', os.path.basename(tmpfilename)]
        cmd += self._option('--max-overall-download-limit', 'ratelimit')
        cmd += self._option('--interface', 'source_address')
        cmd += self._option('--all-proxy', 'proxy')
        cmd += self._bool_option('--check-certificate', 'nocheckcertificate', 'false', 'true', '=')
        cmd += self._bool_option('--remote-time', 'updatetime', 'true', 'false', '=')
        cmd += self._bool_option('--show-console-readout', 'noprogress', 'false', 'true', '=')
        cmd += self._configuration_args()

        # aria2c strips out spaces from the beginning/end of filenames and paths.
        # We work around this issue by adding a "./" to the beginning of the
        # filename and relative path, and adding a "/" at the end of the path.
        # See: https://github.com/yt-dlp/yt-dlp/issues/276
        # https://github.com/ytdl-org/youtube-dl/issues/20312
        # https://github.com/aria2/aria2/issues/1373
        dn = os.path.dirname(tmpfilename)
        if dn:
            cmd += ['--dir', self._aria2c_filename(dn) + os.path.sep]
        if 'fragments' not in info_dict:
            cmd += ['--out', self._aria2c_filename(os.path.basename(tmpfilename))]
        cmd += ['--auto-file-renaming=false']
        if 'fragments' in info_dict:
            cmd += ['--file-allocation=none', '--uri-selector=inorder']
            url_list_file = '%s.frag.urls' % (tmpfilename, )
            url_list = []
            for frag_index, fragment in enumerate(info_dict['fragments']):
                fragment_filename = '%s-Frag%d' % (os.path.basename(tmpfilename), frag_index)
                url_list.append('%s\n\tout=%s' % (fragment['url'], self._aria2c_filename(fragment_filename)))
            stream, _ = self.sanitize_open(url_list_file, 'wb')
            stream.write('\n'.join(url_list).encode())
            stream.close()
            cmd += ['-i', self._aria2c_filename(url_list_file)]
        else:
            cmd += ['--', info_dict['url']]
        return cmd