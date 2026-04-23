def _finish_frag_download(self, ctx):
        ctx['dest_stream'].close()
        if self.__do_ytdl_file(ctx):
            ytdl_filename = encodeFilename(self.ytdl_filename(ctx['filename']))
            if os.path.isfile(ytdl_filename):
                os.remove(ytdl_filename)
        elapsed = time.time() - ctx['started']

        if ctx['tmpfilename'] == '-':
            downloaded_bytes = ctx['complete_frags_downloaded_bytes']
        else:
            self.try_rename(ctx['tmpfilename'], ctx['filename'])
            if self.params.get('updatetime', True):
                filetime = ctx.get('fragment_filetime')
                if filetime:
                    try:
                        os.utime(ctx['filename'], (time.time(), filetime))
                    except Exception:
                        pass
            downloaded_bytes = self.filesize_or_none(ctx['filename']) or 0

        self._hook_progress({
            'downloaded_bytes': downloaded_bytes,
            'total_bytes': downloaded_bytes,
            'filename': ctx['filename'],
            'status': 'finished',
            'elapsed': elapsed,
        })