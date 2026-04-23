def _prepare_frag_download(self, ctx):
        if not ctx.setdefault('live', False):
            total_frags_str = '%d' % ctx['total_frags']
            ad_frags = ctx.get('ad_frags', 0)
            if ad_frags:
                total_frags_str += ' (not including %d ad)' % ad_frags
        else:
            total_frags_str = 'unknown (live)'
        self.to_screen(
            '[%s] Total fragments: %s' % (self.FD_NAME, total_frags_str))
        self.report_destination(ctx['filename'])
        continuedl = self.params.get('continuedl', True)
        dl = HttpQuietDownloader(
            self.ydl,
            {
                'continuedl': continuedl,
                'quiet': True,
                'noprogress': True,
                'ratelimit': self.params.get('ratelimit'),
                'retries': self.params.get('retries', 0),
                'nopart': self.params.get('nopart', False),
                'test': self.params.get('test', False),
            }
        )
        tmpfilename = self.temp_name(ctx['filename'])
        open_mode = 'wb'

        # Establish possible resume length
        resume_len = self.filesize_or_none(tmpfilename) or 0
        if resume_len > 0:
            open_mode = 'ab'

        # Should be initialized before ytdl file check
        ctx.update({
            'tmpfilename': tmpfilename,
            'fragment_index': 0,
        })

        if self.__do_ytdl_file(ctx):
            ytdl_file_exists = os.path.isfile(encodeFilename(self.ytdl_filename(ctx['filename'])))
            if continuedl and ytdl_file_exists:
                self._read_ytdl_file(ctx)
                is_corrupt = ctx.get('ytdl_corrupt') is True
                is_inconsistent = ctx['fragment_index'] > 0 and resume_len == 0
                if is_corrupt or is_inconsistent:
                    message = (
                        '.ytdl file is corrupt' if is_corrupt else
                        'Inconsistent state of incomplete fragment download')
                    self.report_warning(
                        '%s. Restarting from the beginning...' % message)
                    ctx['fragment_index'] = resume_len = 0
                    if 'ytdl_corrupt' in ctx:
                        del ctx['ytdl_corrupt']
                    self._write_ytdl_file(ctx)

            else:
                if not continuedl:
                    if ytdl_file_exists:
                        self._read_ytdl_file(ctx)
                    ctx['fragment_index'] = resume_len = 0
                self._write_ytdl_file(ctx)
                assert ctx['fragment_index'] == 0

        dest_stream, tmpfilename = sanitize_open(tmpfilename, open_mode)

        ctx.update({
            'dl': dl,
            'dest_stream': dest_stream,
            'tmpfilename': tmpfilename,
            # Total complete fragments downloaded so far in bytes
            'complete_frags_downloaded_bytes': resume_len,
        })