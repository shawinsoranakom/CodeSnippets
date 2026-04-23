def real_download(self, filename, info_dict):
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)
        self._cookies_tempfile = None

        try:
            started = time.time()
            retval = self._call_downloader(tmpfilename, info_dict)
        except KeyboardInterrupt:
            if not info_dict.get('is_live'):
                raise
            # Live stream downloading cancellation should be considered as
            # correct and expected termination thus all postprocessing
            # should take place
            retval = 0
            self.to_screen('[%s] Interrupted by user' % self.get_basename())
        finally:
            if self._cookies_tempfile and os.path.isfile(self._cookies_tempfile):
                try:
                    os.remove(self._cookies_tempfile)
                except OSError:
                    self.report_warning(
                        'Unable to delete temporary cookies file "{0}"'.format(self._cookies_tempfile))

        if retval == 0:
            status = {
                'filename': filename,
                'status': 'finished',
                'elapsed': time.time() - started,
            }
            if filename != '-':
                fsize = os.path.getsize(encodeFilename(tmpfilename))
                self.to_screen('\r[%s] Downloaded %s bytes' % (self.get_basename(), fsize))
                self.try_rename(tmpfilename, filename)
                status.update({
                    'downloaded_bytes': fsize,
                    'total_bytes': fsize,
                })
            self._hook_progress(status)
            return True
        else:
            self.to_stderr('\n')
            self.report_error('%s exited with code %d' % (
                self.get_basename(), retval))
            return False