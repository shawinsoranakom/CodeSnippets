def _finish_frag_download(self, ctx, info_dict):
        ctx['dest_stream'].close()
        if self.__do_ytdl_file(ctx):
            self.try_remove(self.ytdl_filename(ctx['filename']))
        elapsed = time.time() - ctx['started']

        to_file = ctx['tmpfilename'] != '-'
        if to_file:
            downloaded_bytes = self.filesize_or_none(ctx['tmpfilename'])
        else:
            downloaded_bytes = ctx['complete_frags_downloaded_bytes']

        if not downloaded_bytes:
            if to_file:
                self.try_remove(ctx['tmpfilename'])
            self.report_error('The downloaded file is empty')
            return False
        elif to_file:
            self.try_rename(ctx['tmpfilename'], ctx['filename'])
            filetime = ctx.get('fragment_filetime')
            if self.params.get('updatetime') and filetime:
                with contextlib.suppress(Exception):
                    os.utime(ctx['filename'], (time.time(), filetime))

        self._hook_progress({
            'downloaded_bytes': downloaded_bytes,
            'total_bytes': downloaded_bytes,
            'filename': ctx['filename'],
            'status': 'finished',
            'elapsed': elapsed,
            'ctx_id': ctx.get('ctx_id'),
            'max_progress': ctx.get('max_progress'),
            'progress_idx': ctx.get('progress_idx'),
        }, info_dict)
        return True